import json
import os
from pathlib import Path

from common.utils import JsonDict

BASE_PATH = Path(os.getenv("PROJECT_BASE_PATH"))

CONFIG_BASE_PATH = Path(os.getenv("CONFIG_DIR"))


def get_service_path(service_path: str) -> Path:
    if service_path is None:
        return BASE_PATH
    return BASE_PATH / service_path


def get_config_path(service_path: str) -> Path:
    if service_path is None:
        return CONFIG_BASE_PATH
    return CONFIG_BASE_PATH / service_path


def get_service_and_config_paths(service_directory: str) -> tuple[Path, Path]:
    return get_service_path(service_directory), get_config_path(service_directory)


def load_config_json(config_path: Path) -> JsonDict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)
