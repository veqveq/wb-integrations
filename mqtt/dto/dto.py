from common.utils import JsonDict


class MQTTConfig:
    def __init__(self, json: JsonDict):
        self.host = json.get("host")
        self.port = json.get("port")
        self.client_id = json.get("clientId")
