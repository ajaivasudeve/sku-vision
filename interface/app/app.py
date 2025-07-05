import streamlit as st
import requests
from PIL import Image, ImageDraw
import random
from collections import defaultdict
from src.util.settings import Settings
from src.util.logger import get_logger

settings = Settings()
logger = get_logger(__name__)

SERVER_URL = settings.server_url
TIMEOUT = settings.request_timeout

st.set_page_config(page_title="Product Detector", layout="centered")
st.title("🧠 Product Detection Interface")
st.markdown("Upload a retail shelf image and see detected products.")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    uploaded_file.seek(0)
    image = Image.open(uploaded_file).convert("RGB")

    if st.button("🔍 Detect Products"):
        st.info("Sending image to server...")
        logger.info("Sending image '%s' to %s", uploaded_file.name, SERVER_URL)

        try:
            uploaded_file.seek(0)
            files = {
                "image": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)
            }
            response = requests.post(SERVER_URL, files=files, timeout=TIMEOUT)
            response.raise_for_status()

            result = response.json()
            detections = result.get("detections", [])
            logger.info("Detection successful: %d detections", len(detections))
            st.success("Detection complete!")

            label_colors = defaultdict(
                lambda: (
                    random.randint(50, 255),
                    random.randint(50, 255),
                    random.randint(50, 255),
                )
            )

            draw = ImageDraw.Draw(image)
            for det in detections:
                bbox = det["bbox"]
                label = det["label"]
                color = label_colors[label]
                draw.rectangle(bbox, outline=color, width=5)
                draw.text((bbox[0], bbox[1] - 10), label, fill=color)

            st.image(image, caption="Detected Products", use_container_width=True)
            st.markdown("### 📝 Detection Results")
            st.json(result)

        except requests.RequestException as e:
            logger.exception("Request failed: %s", e)
            st.error("Something went wrong!")

        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            st.error("Something went wrong!")
