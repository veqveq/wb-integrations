import logging
import sys
from logging import Logger, Formatter, FileHandler, StreamHandler
from pathlib import Path


def configure_logger(name: str, log_path: Path) -> Logger:
    log_path.mkdir(parents=True, exist_ok=True)

    logger: Logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    formatter: Formatter = Formatter(
        "%(asctime)s | %(levelname)s | [%(name)s] %(message)s"
    )

    file_handler = FileHandler(log_path / f'{name}.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
