import json
from pathlib import Path

from common.utils import JsonDict


def load_config_json(config_path: Path) -> JsonDict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)
