from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s -"
        " %(levelname)s -"
        " %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )
    host: str = "0.0.0.0"
    port: int = 5005
    debug: bool = False

    class Config:
        env_prefix = "DETECTOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"
