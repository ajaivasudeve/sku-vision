from flask import Flask
from src.blueprints.detector import detector_bp
from src.util.logger import get_logger
from src.util.settings import Settings

settings = Settings()
logger = get_logger(__name__)

app = Flask(__name__)
app.register_blueprint(detector_bp, url_prefix="/")
logger.info("Blueprint registered and app created.")

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
