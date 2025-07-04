## 📌 Server Endpoint (Flask Blueprint)

**URL:** `/process`
**Method:** `POST`
**Purpose:** End-to-end pipeline that detects, groups, merges, and summarizes product detections from a retail shelf image.

---

### ✅ Input (multipart/form-data)

* **image**: A valid image file (`.jpg`, `.jpeg`, `.png`, etc.)

---

### 📤 Output (JSON)

```json
{
  "detections": [
    {
      "label": "cluster_<id>" | "noise",
      "bbox": [x1, y1, x2, y2]
    },
    ...
  ],
  "metadata": {
    "cluster_counts": {
      "cluster_0": 5,
      "cluster_1": 3,
      "noise": 12
    },
    "total_clusters": 3
  }
}
```

* `detections`: Final merged bounding boxes grouped by visual similarity.
* `metadata.cluster_counts`: Number of products in each cluster (including "noise").
* `metadata.total_clusters`: Total unique cluster labels (including "noise").

---

### ⚙️ Pipeline Steps

1. Sends the uploaded image to the `/detect` service (DETR model) for object detection.
2. Forwards detections and image to `/group` (HDBSCAN clustering based on visual features).
3. Merges overlapping boxes within each cluster using an IoU threshold of 0.33.
4. Counts how many detections belong to each cluster.

---

### ❗ Error Responses

* `400`: Missing image in request.
* `500`: Failure in calling detector/grouper service or unexpected internal error.

---

