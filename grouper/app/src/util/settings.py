from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s -"
        " %(levelname)s -"
        " %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )
    host: str = "0.0.0.0"
    port: int = 5003
    debug: bool = False
    luminance_normalization: bool = False
    apply_clahe: bool = True
    downsample_resolution: int = 28

    class Config:
        env_prefix = "DETECTOR_"
        env_file = ".env"
        env_file_encoding = "utf-8"
