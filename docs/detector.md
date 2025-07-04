## 📌 Detector Endpoint (Flask Blueprint)

**URL:** `/detect`
**Method:** `POST`
**Purpose:** Run object detection on an input image using a fine-tuned DETR model (`isalia99/detr-resnet-50-sku110k`).

---

### ✅ Input (multipart/form-data)

* **image**: A valid image file (`.jpg`, `.png`, etc.).

---

### 📤 Output (JSON)

```json
{
  "detections": [
    {
      "label": "<class_name>",
      "score": 0.987,
      "bbox": [x1, y1, x2, y2]
    },
    ...
  ]
}
```

* Boxes are in **absolute pixel coordinates**.
* Only detections with `score >= 0.8` are returned.

---

### ⚙️ Processing Steps

1. Image is read, corrected for EXIF orientation.
2. Run through `DetrImageProcessor` and `DetrForObjectDetection`.
3. Post-processed with confidence thresholding (`0.8`).
4. Outputs a list of class-labeled bounding boxes.

---

### ❗ Error Responses

* `400`: No image or invalid image.
* `500`: Internal server error.

---