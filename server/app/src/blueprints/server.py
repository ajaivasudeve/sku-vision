from flask import Blueprint, request, jsonify
import requests
from src.util.logger import get_logger
from src.util.settings import Settings
import json

server_bp = Blueprint("server", __name__)
logger = get_logger(__name__)
settings = Settings()

DETECTOR_URL = settings.detector_url
GROUPER_URL = settings.grouper_url

@server_bp.route("/process", methods=["POST"])
def process_image():
    if "image" not in request.files:
        logger.warning("No image part in the request")
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    try:
        logger.info("Forwarding image to detector service at %s", DETECTOR_URL)
        image_bytes = file.read()
        detector_response = requests.post(
            DETECTOR_URL,
            files={"image": (file.filename, image_bytes, file.mimetype)},
            timeout=30
        )
        detector_response.raise_for_status()
        detections_json = detector_response.json()
        logger.info("Detector returned %d detections", len(detections_json.get("detections", [])))

        logger.info("Forwarding detection result to grouper at %s", GROUPER_URL)
        grouper_response = requests.post(
            GROUPER_URL,
            files={"image": (file.filename, image_bytes, file.mimetype)},
            data={"detections": json.dumps(detections_json["detections"])},
            timeout=30
        )
        grouper_response.raise_for_status()
        grouped_json = grouper_response.json()
        logger.info("Received grouped detections")

        return jsonify(grouped_json)

    except requests.RequestException as e:
        logger.exception("HTTP call failed: %s", e)
        return jsonify({"error": "Failed to contact downstream service"}), 500

    except Exception as e:
        logger.exception("Unexpected error in /process: %s", e)
        return jsonify({"error": "Internal server error"}), 500
