# 🧠 Product Detection & Grouping

A modular microservice-based system for detecting and grouping products in retail shelf images. Upload an image and get clean, grouped bounding boxes via a simple web interface.

---

## 🚀 Getting Started

### 1. Start the System

```bash
docker compose up
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
