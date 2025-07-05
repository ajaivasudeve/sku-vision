from flask import Blueprint, request, jsonify
from PIL import Image, UnidentifiedImageError
import numpy as np
import cv2
import json
from io import BytesIO
from sklearn.cluster import HDBSCAN
from src.util.logger import get_logger
from src.util.settings import Settings

grouper_bp = Blueprint("grouper", __name__)
logger = get_logger(__name__)
settings = Settings()


def normalize_luminance(pil_image, apply_clahe=False):
    try:
        logger.info("Starting luminance normalization (CLAHE=%s)", apply_clahe)

        img_rgb = np.array(pil_image)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2Lab)
        l, a, b = cv2.split(lab)

        l_float = l.astype(np.float32)
        blurred_l = cv2.GaussianBlur(l_float, (101, 101), 0) + 1e-6

        l_norm = l_float / blurred_l
        l_norm *= np.mean(l_float) / np.mean(l_norm)
        l_norm = np.clip(l_norm, 0, 255).astype(np.uint8)

        if apply_clahe:
            logger.info("Applying CLAHE")
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_norm = clahe.apply(l_norm)

        a = np.clip(a, 0, 255).astype(np.uint8)
        b = np.clip(b, 0, 255).astype(np.uint8)

        lab_corrected = cv2.merge([l_norm, a, b])
        corrected_bgr = cv2.cvtColor(lab_corrected, cv2.COLOR_Lab2BGR)
        corrected_rgb = cv2.cvtColor(corrected_bgr, cv2.COLOR_BGR2RGB)

        logger.info("Luminance normalization completed successfully")
        return Image.fromarray(corrected_rgb)

    except Exception as e:
        logger.exception("Error during luminance normalization: %s", e)
        return pil_image


@grouper_bp.route("/group", methods=["POST"])
def group_detections():
    try:
        if "image" not in request.files or "detections" not in request.form:
            return jsonify({"error": "Missing image or detections"}), 400

        try:
            image = Image.open(BytesIO(request.files["image"].read())).convert("RGB")
        except UnidentifiedImageError:
            return jsonify({"error": "Invalid image"}), 400

        if settings.luminance_normalization:
            image = normalize_luminance(image, apply_clahe=settings.apply_clahe)

        try:
            detections = json.loads(request.form["detections"])
            boxes = [d["bbox"] for d in detections]
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid detections JSON"}), 400

        features = []
        valid_indices = []

        for i, box in enumerate(boxes):
            try:
                x1, y1, x2, y2 = map(int, box)
                crop = image.crop((x1, y1, x2, y2)).resize(
                    (settings.downsample_resolution, settings.downsample_resolution),
                    resample=Image.BOX,
                )
                arr = np.asarray(crop).astype(np.float32) / 255.0
                features.append(arr.flatten())
                valid_indices.append(i)
            except Exception:
                logger.warning("Failed to process crop %d", i)

        if not features:
            return jsonify({"error": "No valid features"}), 400

        X = np.vstack(features)

        clusterer = HDBSCAN(
            metric="euclidean",
            min_cluster_size=2,
            min_samples=2,
            cluster_selection_method="eom",
        )
        labels = clusterer.fit_predict(X)

        for idx, cid in zip(valid_indices, labels):
            detections[idx]["label"] = f"cluster_{cid}" if cid != -1 else "noise"

        return jsonify({"detections": detections})
    except Exception as e:
        logger.exception("Internal error in /group: %s", e)
        return jsonify({"error": "Internal server error"}), 500
