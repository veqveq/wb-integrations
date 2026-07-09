from requests import Session, Response

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from common.utils import JsonDict
from keenetic.dto.dto import KeeneticRouterConfig, NetworkClient

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("keenetic")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
ENDPOINTS_FILE = CONFIG_PATH / "endpoints.json"

LOGGER = configure_logger("logs", LOG_PATH)


class KeeneticRouter:
    def __init__(self):
        config: KeeneticRouterConfig = KeeneticRouterConfig(load_config_json(SETTINGS_FILE))
        endpoints: JsonDict = load_config_json(ENDPOINTS_FILE)
        self.endpoints: dict[str, str] = {k: f"https://{config.host}{v}" for k, v in endpoints.items()}
        self.session: Session = Session()
        self.session.auth = (config.username, config.password)
        self.session.headers.update({"Accept": "application/json"})

    def get_clients(self) -> list[NetworkClient]:
        try:
            response: Response = self.session.get(f"{self.endpoints.get("getClients")}", timeout=10)
            response.raise_for_status()
            LOGGER.debug(f"GET CLIENTS: {response.json()}")

            host: list[JsonDict] = response.json().get("host", [])
            return [NetworkClient(client) for client in host]
        except Exception:
            LOGGER.error("GET CLIENTS error", exc_info=True)

    def close(self):
        self.session.close()
        LOGGER.debug("Router disconnected...")
