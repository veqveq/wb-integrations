from typing import Any

import requests

from common.config_loader import load_config_json
from common.logger import configure_logger
from common.utils import BASE_PATH, JsonDict
from keenetic.dto.dto import KeeneticRouterConfig, NetworkClient

PATH = BASE_PATH / "keenetic"
LOG_PATH = PATH / "logs"
CONFIG_PATH = PATH / "config"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
ENDPOINTS_FILE = CONFIG_PATH / "endpoints.json"

LOGGER = configure_logger("KEENETIC_ROUTER", LOG_PATH)


class KeeneticRouter:
    def __init__(self):
        config: KeeneticRouterConfig = KeeneticRouterConfig(load_config_json(SETTINGS_FILE))
        endpoints: JsonDict = load_config_json(ENDPOINTS_FILE)
        self.endpoints = {k: f"https://{config.host}{v}" for k, v in endpoints.items()}
        self.session = requests.Session()
        self.session.auth = (config.username, config.password)
        self.session.headers.update({"Accept": "application/json"})

    def get_clients(self) -> list[NetworkClient]:
        try:
            response = self.session.get(f"{self.endpoints.get("getClients")}", timeout=10)
            response.raise_for_status()
            LOGGER.debug(f"GET CLIENTS: {response.json()}")
            host = response.json().get("host", [])
            return [NetworkClient(client) for client in host]
        except Exception:
            LOGGER.error("GET CLIENTS error", exc_info=True)

    def close(self):
        self.session.close()
        LOGGER.debug("Router disconnected...")
