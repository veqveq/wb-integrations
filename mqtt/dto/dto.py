from common.utils import JsonDict


class MQTTConfig:
    def __init__(self, json: JsonDict):
        self.host = json.get("host")
        self.port = json.get("port")
        self.client_id = json.get("clientId")


class MQTTDeviceConfig:
    def __init__(self, json: JsonDict):
        self.device_name = json["deviceName"]
        self.controls = json.get("controls", {})
