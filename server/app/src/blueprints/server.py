from flask import Blueprint, request, jsonify
import requests
from src.util.logger import get_logger
from src.util.settings import Settings

server_bp = Blueprint("server", __name__)
logger = get_logger(__name__)
settings = Settings()

DETECTOR_URL = settings.detector_url

@server_bp.route("/process", methods=["POST"])
def process_image():
    if "image" not in request.files:
        logger.warning("No image part in the request")
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]

    try:
        logger.info("Forwarding image to detector service at %s", DETECTOR_URL)
        response = requests.post(
            DETECTOR_URL,
            files={"image": (file.filename, file.read(), file.mimetype)},
            timeout=30
        )
        response.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Error contacting detector: %s", e)
        return jsonify({"error": "Failed to contact detector service"}), 500

    logger.info("Received response from detector with status %d", response.status_code)
    return jsonify(response.json())
