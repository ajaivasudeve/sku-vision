from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = (
        "%(asctime)s -"
        " %(levelname)s -"
        " %(filename)s:%(lineno)d - %(name)s - %(message)s"
    )
    debug: bool = False
    server_url: str = "http://server:5000/process"
    request_timeout: float = 300

    class Config:
        env_prefix = "INTERFACE_"
        env_file = ".env"
        env_file_encoding = "utf-8"
