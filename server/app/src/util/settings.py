from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s -"
        " %(levelname)s -"
        " %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    detector_url: str = "http://detector:5001/detect"
    grouper_url: str = "http://grouper:5003/group"
    detector_timeout: float = 300
    grouper_timeout: float = 300

    class Config:
        env_prefix = "SERVER_"
        env_file = ".env"
        env_file_encoding = "utf-8"
