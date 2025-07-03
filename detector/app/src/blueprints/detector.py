from io import BytesIO
from flask import Blueprint, request, jsonify
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image, ImageOps, UnidentifiedImageError
from src.util.logger import get_logger
import torch

detector_bp = Blueprint("detector", __name__)
logger = get_logger(__name__)

try:
    processor: DetrImageProcessor = DetrImageProcessor.from_pretrained(
        "facebook/detr-resnet-50", revision="no_timm"
    )
    model = DetrForObjectDetection.from_pretrained("isalia99/detr-resnet-50-sku110k")
    model.eval()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    logger.info("Detection model and processor loaded successfully on device: %s", device)

except Exception as e:
    logger.exception("Failed to load DETR model or processor: %s", e)
    raise RuntimeError("Model initialization failed") from e


@detector_bp.route("/detect", methods=["POST"])
def detect():
    try:
        if "image" not in request.files:
            logger.warning("No image part in the request")
            return jsonify({"error": "No image provided"}), 400

        file = request.files["image"]

        try:
            image = Image.open(BytesIO(file.read()))
            image = ImageOps.exif_transpose(image)
        except UnidentifiedImageError:
            logger.warning("Invalid image file received")
            return jsonify({"error": "Invalid image file"}), 400

        # Prepare image for model
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        target_sizes = torch.tensor([image.size[::-1]]).to(device)
        results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.8)[0]

        detections = []
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"]
        ):
            box = [round(i, 2) for i in box.tolist()]
            detections.append({
                "label": model.config.id2label[label.item()],
                "score": round(score.item(), 3),
                "bbox": box
            })

        logger.info("Detected %d objects", len(detections))
        return jsonify({"detections": detections})

    except Exception as e:
        logger.exception("Unexpected error in /detect: %s", e)
        return jsonify({"error": "Internal server error"}), 500
