from flask import Blueprint, request, jsonify
from PIL import Image, UnidentifiedImageError
import torch
import numpy as np
import json
from io import BytesIO
from sklearn.metrics.pairwise import cosine_distances
from sklearn.cluster import HDBSCAN
from transformers import AutoImageProcessor, AutoModel
from src.util.logger import get_logger

grouper_bp = Blueprint("grouper", __name__)
logger = get_logger(__name__)

try:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base", use_fast=True)
    model = AutoModel.from_pretrained("facebook/dinov2-base").to(device)
    model.eval()
    patch_size = model.config.patch_size
    logger.info("DINOv2 patch model loaded on %s", device)
except Exception as e:
    logger.exception("Failed to load DINOv2 model: %s", e)
    raise RuntimeError("DINOv2 load failed") from e

@grouper_bp.route("/group", methods=["POST"])
def group_detections():
    try:
        if "image" not in request.files or "detections" not in request.form:
            return jsonify({"error": "Missing image or detections"}), 400

        try:
            image = Image.open(BytesIO(request.files["image"].read())).convert("RGB")
        except UnidentifiedImageError:
            return jsonify({"error": "Invalid image"}), 400

        try:
            detections = json.loads(request.form["detections"])
            boxes = [d["bbox"] for d in detections]
        except json.JSONDecodeError as e:
            return jsonify({"error": "Invalid detections JSON"}), 400

        embeddings = []
        valid_indices = []

        for i, box in enumerate(boxes):
            try:
                x1, y1, x2, y2 = map(int, box)
                crop = image.crop((x1, y1, x2, y2))
                inputs = processor(images=crop, return_tensors="pt").to(device)
                with torch.no_grad():
                    out = model(**inputs)
                    tokens = out.last_hidden_state
                    patch_tokens = tokens[:, 1:, :]
                    h = int(224 / patch_size)
                    patch_tokens = patch_tokens.view(1, h, h, -1)
                    patch_features = patch_tokens.mean(dim=(1, 2))
                    features = torch.nn.functional.normalize(patch_features, dim=1)
                embeddings.append(features.cpu().numpy().flatten())
                valid_indices.append(i)
            except Exception:
                logger.warning("Failed to embed crop %d", i)

        if not embeddings:
            return jsonify({"error": "No valid embeddings"}), 400

        X = np.vstack(embeddings)
        dist = cosine_distances(X)

        clusterer = HDBSCAN(
            metric="precomputed",
            min_cluster_size=2,
            min_samples=2,
            cluster_selection_method="eom"
        )
        labels = clusterer.fit_predict(dist)

        for idx, cid in zip(valid_indices, labels):
            detections[idx]["label"] = f"cluster_{cid}"

        return jsonify({"detections": detections})
    except Exception as e:
        logger.exception("Internal error in /group: %s", e)
        return jsonify({"error": "Internal server error"}), 500
