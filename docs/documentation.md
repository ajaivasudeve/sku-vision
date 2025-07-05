# 🧠 Problem Statement and Solution Overview

## 🚀 Summary

The objective of this assignment was to develop a modular system for product detection and grouping from retail shelf images. The system was required to identify individual product instances and group visually similar items under shared cluster identifiers. Given the 24-hour delivery timeline, the design emphasized speed of implementation, clean modularity, and computational efficiency.

---

## 📌 Step 1: Detection Model Selection

The initial idea was to fine-tune a custom object detector using the SKU110K dataset. However, given the time constraint, this was not viable. Instead, I opted for a robust pre-trained model readily available on Hugging Face:

**[isalia99/detr-resnet-50-sku110k](https://huggingface.co/isalia99/detr-resnet-50-sku110k)**

This model, based on DETR and fine-tuned on SKU110K, performed well on shelf images with a wide variety of product layouts. It was wrapped as a Flask microservice that accepts image input and returns bounding boxes, class labels, and detection confidence scores.

---

## 📌 Step 2: Grouping Strategy Design

With reliable detection in place, the next step was to group the detected product crops based on visual similarity. The goal was to group instances of the same SKU under a single identifier, even if they appeared at different positions or scales in the image.

Initially, I explored the use of vision-language models like CLIP to generate high-dimensional semantic embeddings for each crop. However, running multiple transformer-based models concurrently in a containerized setup proved too resource-intensive for the available environment.

---

## 🧩 Step 3: Lightweight Visual Embedding

To work around the resource limitations, I adopted a lightweight visual embedding strategy based on traditional image processing:

* Each detection crop was resized to a fixed resolution of **28×28 pixels**.
* The image was normalized and flattened into a 1D array of pixel intensities.
* These arrays served as basic visual feature vectors for clustering.

While this method does not capture deep semantic features, it proved effective at capturing basic visual structure — such as dominant color, shape, and layout — which was sufficient for many intra-image grouping tasks. Most importantly, it kept the system fast and responsive.

---

## 📌 Step 4: Clustering with HDBSCAN

Since the number of unique product types per image is unknown and variable, I selected a clustering algorithm that does not require the number of clusters to be specified up front.

After experimentation, the following options were considered:

| Algorithm         | Verdict                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------- |
| **HDBSCAN**       | ✅ Chosen. Automatically determines cluster structure and handles noise/outliers effectively. |
| **DBSCAN**        | ✅ Considered. Performed reasonably but less adaptive to variable density.                    |
| **Agglomerative** | ❌ Rejected. Unstable and highly sensitive to parameter choices.                              |

**HDBSCAN** emerged as the most suitable clustering strategy — offering stable, density-aware clustering with minimal parameter tuning.

---

# Components and Architecture

## 🧩 Microservices Overview

| Service     | Description                                               |
| ----------- | --------------------------------------------------------- |
| `detector`  | Runs product detection using a fine-tuned DETR model      |
| `grouper`   | Clusters visually similar detections using HDBSCAN        |
| `server`    | Orchestrates detection → grouping → merging               |
| `interface` | Streamlit UI for uploading images and visualizing results |

Each service is containerized and exposed via REST APIs.

## 📌 Streamlit Interface: Product Detection

**Purpose:**
Frontend web app for uploading an image and visualizing product detections from a retail shelf.

---

### 🖼️ Functionality

* Uploads an image (`.jpg`, `.jpeg`, `.png`).
* Sends it to the `/process` endpoint of the backend server.
* Displays bounding boxes and cluster labels on the image.
* Shows detection results in JSON format.

---

### ⚙️ Backend Interaction

* **URL:** `POST <server_url>/process`
* **Payload:** Image file
* **Response:**

  ```json
  {
    "detections": [
      {"bbox": [...], "label": "cluster_0"},
      ...
    ]
  }
  ```

---

### 🎨 Visualization

* Draws bounding boxes using randomly assigned colors per cluster label.
* Overlays cluster label text near top-left of each box.
* Full image + results shown in the UI.

---

### ❗ Error Handling

* Shows error messages for request failures or unexpected exceptions.
* Logs all key events using the internal logger.

---

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

To further improve detection robustness and grouping accuracy, the following enhancements are planned or under active consideration:

### 🖼️ Advanced Image Preprocessing

Enhance shelf image consistency and model input quality through preprocessing techniques such as:

* **Luminance Normalization (In Progress):**
  Normalize brightness variations by converting to Lab color space, isolating the L (lightness) channel, and applying Gaussian-blur division.
  Optionally use **CLAHE** to boost local contrast.

  > ✅ Implemented and configurable, but currently disabled pending parameter fine-tuning.

* **Layout-Aware Refinement:**
  Use OpenCV features like **contour detection**, **edge maps**, and **Hough lines** to extract structural cues and better infer shelf layout (e.g. columns, grids). This can help refine regions passed to the detection model or inform grouping logic.

### 🎯 Detection Model Enhancements

* **Fine-Tuned Detection:**
  Fine-tune DETR (or similar) models using images enhanced with custom preprocessing — improving resilience to occlusion, glare, and perspective distortion common in real-world retail scenes.

### 🧠 Smarter Grouping

* **OCR-Based Clustering:**
  Extract text (e.g. brand names, SKUs) using OCR to complement visual embeddings. Especially useful when visually similar products are semantically distinct.

* **Multi-Modal Clustering (If Time Permitted):**
  Combine **visual and textual embeddings** using NLP techniques for semantic-aware clustering. Shelf tags and product labels (via OCR) can be transformed into sentence embeddings and fused with visual features to distinguish similar-looking items.


---
