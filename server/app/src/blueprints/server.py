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
DETECTOR_TIMEOUT = settings.detector_timeout
GROUPER_TIMEOUT = settings.grouper_timeout


def compute_iou(boxA, boxB):
    try:
        x1 = max(boxA[0], boxB[0])
        y1 = max(boxA[1], boxB[1])
        x2 = min(boxA[2], boxB[2])
        y2 = min(boxA[3], boxB[3])

        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        if inter_area == 0:
            return 0.0

        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        union_area = areaA + areaB - inter_area

        return inter_area / union_area
    except Exception as e:
        logger.warning("Failed to compute IoU for boxes %s and %s: %s", boxA, boxB, e)
        return 0.0


def merge_grouped_boxes(detections, iou_threshold=0.7):
    merged_by_cluster = {}
    for d in detections:
        label = d.get("label", "noise")
        merged_by_cluster.setdefault(label, []).append(d["bbox"])

    final_detections = []
    logger.info(
        "Starting merge of grouped boxes with IoU threshold %.2f", iou_threshold
    )

    for label, boxes in merged_by_cluster.items():
        logger.info("Processing cluster '%s' with %d boxes", label, len(boxes))
        used = [False] * len(boxes)

        for i, box_i in enumerate(boxes):
            if used[i]:
                continue
            try:
                x1, y1, x2, y2 = box_i
                merged_box = [x1, y1, x2, y2]

                for j, box_j in enumerate(boxes[i + 1:], start=i + 1):
                    if used[j]:
                        continue
                    iou = compute_iou(merged_box, box_j)
                    if iou >= iou_threshold:
                        logger.info(
                            "Merging box %s with %s (IoU=%.2f)", merged_box, box_j, iou
                        )
                        merged_box[0] = min(merged_box[0], box_j[0])
                        merged_box[1] = min(merged_box[1], box_j[1])
                        merged_box[2] = max(merged_box[2], box_j[2])
                        merged_box[3] = max(merged_box[3], box_j[3])
                        used[j] = True

                used[i] = True
                final_detections.append({"bbox": merged_box, "label": label})
            except Exception as e:
                logger.warning(
                    "Failed to merge box index %d in cluster '%s': %s", i, label, e
                )

    logger.info(
        "Box merging completed. Final merged box count: %d", len(final_detections)
    )
    return final_detections


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
            timeout=DETECTOR_TIMEOUT,
        )
        detector_response.raise_for_status()
        detections_json = detector_response.json()
        logger.info(
            "Detector returned %d detections",
            len(detections_json.get("detections", [])),
        )

        detections = detections_json.get("detections", [])
        if not detections:
            logger.info("No detections found, skipping grouping step")
            return jsonify({
                "detections": [],
                "metadata": {
                    "cluster_counts": {},
                    "total_clusters": 0,
                },
            })

        logger.info("Forwarding detection result to grouper at %s", GROUPER_URL)
        grouper_response = requests.post(
            GROUPER_URL,
            files={"image": (file.filename, image_bytes, file.mimetype)},
            data={"detections": json.dumps(detections_json.get("detections", []))},
            timeout=GROUPER_TIMEOUT,
        )
        grouper_response.raise_for_status()
        grouped_json = grouper_response.json()
        logger.info("Received grouped detections")

        detections = grouped_json.get("detections", [])
        merged_detections = merge_grouped_boxes(detections, iou_threshold=0.33)

        cluster_counts = {}
        for d in detections:
            label = d.get("label", "noise")
            cluster_counts[label] = cluster_counts.get(label, 0) + 1

        return jsonify(
            {
                "detections": merged_detections,
                "metadata": {
                    "cluster_counts": cluster_counts,
                    "total_clusters": len(cluster_counts),
                },
            }
        )

    except requests.RequestException as e:
        logger.exception("HTTP call failed: %s", e)
        return jsonify({"error": "Failed to contact downstream service"}), 500

    except Exception as e:
        logger.exception("Unexpected error in /process: %s", e)
        return jsonify({"error": "Internal server error"}), 500
