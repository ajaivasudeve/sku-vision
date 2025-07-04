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