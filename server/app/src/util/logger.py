import logging
from src.util.settings import Settings

settings = Settings()
_loggers = {}
_log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    level_str = settings.log_level.upper()
    log_level = _log_levels.get(level_str, logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter(settings.log_format)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.propagate = False
    _loggers[name] = logger
    return logger
