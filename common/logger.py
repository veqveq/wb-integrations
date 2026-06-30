import logging
import sys

from pathlib import Path
from logging import Logger


def configure_logger(name: str, log_path: Path) -> Logger:
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | [%(name)s] %(message)s"
    )

    file_handler = logging.FileHandler(log_path / f'{name}.log', encoding='utf-8')

    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
