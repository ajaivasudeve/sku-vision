# 🧠 Product Detection & Grouping

A modular microservice-based system for detecting and grouping products in retail shelf images. Upload an image and get clean, grouped bounding boxes via a simple web interface.

---

## 🧩 Microservices Overview

| Service     | Description                                               |
| ----------- | --------------------------------------------------------- |
| `detector`  | Runs product detection using a fine-tuned DETR model      |
| `grouper`   | Clusters visually similar detections using HDBSCAN        |
| `server`    | Orchestrates detection → grouping → merging               |
| `interface` | Streamlit UI for uploading images and visualizing results |

Each service is containerized and exposed via REST APIs.

---

## 🤖 Model Information

> **Model:** [`isalia99/detr-resnet-50-sku110k`](https://huggingface.co/isalia99/detr-resnet-50-sku110k)

### Details:

* Based on `facebook/detr-resnet-50`
* Fine-tuned on [SKU110K](https://github.com/eg4000/SKU110K_CVPR19) — retail product dataset
* Detects densely packed products (no OCR or product metadata needed)
* Used by the `detector` service

---

## 🚀 Getting Started

### 1. Start the System

```bash
docker compose up --build --force-recreate
```

This will build and launch all services.

---

### 2. ⏳ Wait for Services to Register

⚠️ **Don't send requests immediately.**
First requests may fail if services are not ready. Wait for the following log line from each container:

> ```
> Blueprint registered and app created.
> ```

Once this appears for `detector`, `grouper`, and `server`, the system is ready to use.

---

### 3. Open the Web Interface

Visit: [http://localhost:5002](http://localhost:5002)

* Upload a shelf image (`.jpg`, `.jpeg`, or `.png`)
* Click **"🔍 Detect Products"**
* View grouped bounding boxes on the image
* Inspect raw JSON output

---

## 📁 Project Structure

```
detector/         → DETR-based object detection
grouper/          → CLAHE + visual clustering (HDBSCAN)
server/           → Pipeline controller + merging
interface/        → Streamlit-based frontend
docker-compose.yml → Service wiring
```

---

## ⚙️ Design Highlights & Optimizations

* **Efficient Image Preprocessing:**
  Before products are grouped, the system enhances the image to handle lighting and contrast issues. This helps improve consistency across different types of shelf photos.

* **Lightweight Feature Representation:**
  Each detected product is simplified into a compact visual form, which makes comparing and grouping them much faster without needing heavy processing.

* **Unsupervised Visual Grouping:**
  The system can automatically group similar-looking products without needing any manual labeling or predefined categories.

* **IoU-Based Box Merging:**
  If the system finds multiple overlapping boxes that likely belong to the same product group, it smartly combines them into one cleaner result.

* **Cluster-Level Product Count Summary:**
  The final output includes a summary of how many products belong to each group (or cluster). This makes it easier to understand the shelf layout at a glance and supports downstream use cases like audits or inventory tracking.

---

## 🔮 Future Enhancements

Here are some planned improvements that could further boost accuracy and flexibility:

* **Advanced Preprocessing with OpenCV:**
  Use techniques like contour detection, edge maps, and Hough lines to better understand shelf layouts and object boundaries — this can help refine the regions passed to the detection model.

* **Layout-Aware Adjustments:**
  Tailor image preprocessing based on common shelf patterns (e.g. grid-like arrangements, columns) to improve grouping accuracy in real-world scenarios.

* **Fine-Tuned Detection Models:**
  Train or fine-tune detection models using images enhanced through custom preprocessing — making them more robust to retail-specific challenges like occlusion, glare, and skewed angles.

* **OCR-Based Clustering:**
  Use text (e.g. brand names, labels, SKUs) extracted via OCR to complement visual similarity during grouping — especially useful when visually similar products are actually different items.

---

