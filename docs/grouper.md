## 📌 Grouper Endpoint (Flask Blueprint)

**URL:** `/group`
**Method:** `POST`
**Purpose:** Cluster image detections based on visual similarity using HDBSCAN.

---

### ✅ Inputs (multipart/form-data)

* **image**: A valid image file (`.jpg`, `.png`, etc.).
* **detections**: A JSON string of detection objects, each with a `"bbox"`:

  ```json
  {"bbox": [x1, y1, x2, y2]}
  ```

---

### 📤 Output (JSON)

Returns the same list of detections with an added `label`:

```json
{"detections": [{"bbox": [...], "label": "cluster_0" | "noise"}, ...]}
```

---

### ⚙️ Processing Steps

1. Image is preprocessed (luminance normalization + optional CLAHE).
2. Each detection crop is resized, flattened, and feature-extracted.
3. Features are clustered using **HDBSCAN**.
4. Detections are labeled with `cluster_<id>` or `"noise"`.

---

### ❗ Error Responses

* `400`: Missing image or detections, bad JSON, or no valid crops.
* `500`: Unexpected server error.

--- 