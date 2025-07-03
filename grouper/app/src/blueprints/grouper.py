from flask import Blueprint, request, jsonify
from PIL import Image, UnidentifiedImageError
import torch
import numpy as np
import json
from io import BytesIO
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from transformers import AutoProcessor, AutoModel
from src.util.logger import get_logger

grouper_bp = Blueprint("grouper", __name__)
logger = get_logger(__name__)

try:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    processor = AutoProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model = AutoModel.from_pretrained("openai/clip-vit-base-patch32")
    model.to(device)
    model.eval()
    logger.info("CLIP model loaded successfully on %s", device)
except Exception as e:
    logger.exception("Failed to load CLIP model: %s", e)
    raise RuntimeError("CLIP model load failed") from e


@grouper_bp.route("/group", methods=["POST"])
def group_detections():
    try:
        if "image" not in request.files or "detections" not in request.form:
            logger.warning("Missing image or detections in request")
            return jsonify({"error": "Missing image or detections"}), 400

        try:
            image = Image.open(BytesIO(request.files["image"].read())).convert("RGB")
        except UnidentifiedImageError:
            logger.warning("Invalid image file received")
            return jsonify({"error": "Invalid image"}), 400

        try:
            detections = json.loads(request.form["detections"])
            boxes = [d["bbox"] for d in detections]
        except Exception as e:
            logger.warning("Invalid detections JSON: %s", e)
            return jsonify({"error": "Invalid detections JSON"}), 400

        embeddings = []
        valid_indices = []

        for i, box in enumerate(boxes):
            try:
                x1, y1, x2, y2 = map(int, box)
                cropped = image.crop((x1, y1, x2, y2))
                inputs = processor(images=cropped, return_tensors="pt").to(device)
                with torch.no_grad():
                    features = model.get_image_features(**inputs)
                    features = torch.nn.functional.normalize(features, dim=1)
                embeddings.append(features.cpu().numpy().flatten())
                valid_indices.append(i)
            except Exception as e:
                logger.warning("Failed to embed crop %d: %s", i, e)

        if not embeddings:
            return jsonify({"error": "No valid crops for embedding"}), 400

        try:
            X = np.vstack(embeddings)
            dist = cosine_distances(X)
            clusterer = DBSCAN(eps=0.3, min_samples=2, metric="precomputed")
            labels = clusterer.fit_predict(dist)
        except Exception as e:
            logger.exception("Clustering failed: %s", e)
            return jsonify({"error": "Clustering failed"}), 500

        for idx, cluster_id in zip(valid_indices, labels):
            detections[idx]["label"] = f"cluster_{cluster_id}"

        logger.info("Clustered %d detections into %d clusters", len(labels), len(set(labels)))
        return jsonify({"detections": detections})

    except Exception as e:
        logger.exception("Unexpected error in /group: %s", e)
        return jsonify({"error": "Internal server error"}), 500
