import streamlit as st
import requests
from PIL import Image
from src.util.settings import Settings
from src.util.logger import get_logger

# Load settings and logger
settings = Settings()
logger = get_logger(__name__)

SERVER_URL = settings.server_url or "http://localhost:5000/process"

st.set_page_config(page_title="Product Detector", layout="centered")
st.title("🧠 Product Detection Interface")
st.markdown("Upload a retail shelf image and see detected products.")

uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    uploaded_file.seek(0)  # reset stream position
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    if st.button("🔍 Detect Products"):
        st.info("Sending image to server...")
        logger.info("Sending image '%s' to %s", uploaded_file.name, SERVER_URL)

        try:
            uploaded_file.seek(0)
            files = {"image": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)}
            response = requests.post(SERVER_URL, files=files, timeout=30)
            response.raise_for_status()

            result = response.json()
            logger.info("Detection successful: %d detections", len(result.get("detections", [])))

            st.success("Detection complete!")
            st.markdown("### 📝 Detection Results")
            st.json(result)

        except requests.RequestException as e:
            logger.exception("Request failed: %s", e)
            st.error(f"Failed to contact server: {e}")

        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            st.error(f"Something went wrong: {e}")
