from common.utils import JsonDict


class MQTTConfig:
    def __init__(self, json: JsonDict):
        self.host: str = json.get("host")
        self.port: int = json.get("port")
        self.client_id: str = json.get("clientId")
