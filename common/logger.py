import logging
import sys
from logging import Logger
from pathlib import Path


def configure_logger(name: str, log_path: Path) -> Logger:
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | [%(name)s] %(message)s"
    )

    file_handler = logging.FileHandler(log_path / f'{name}.log', encoding='utf-8')

    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
