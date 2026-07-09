from common.utils import JsonDict
from common.wirenboard import WbDeviceMeta


class HikvisionCameraConfig:
    UNKNOWN_CAMERA_COUNTER: int = 0

    @staticmethod
    def get_unknown_camera_name() -> str:
        HikvisionCameraConfig.UNKNOWN_CAMERA_COUNTER += 1
        return f"Камера {HikvisionCameraConfig.UNKNOWN_CAMERA_COUNTER}"

    def __init__(self, json: JsonDict):
        self.name: str = json.get("name", HikvisionCameraConfig.get_unknown_camera_name())
        self.host: str = json["host"]
        self.username: str = json["username"]
        self.password: str = json["password"]
        self.meta: WbDeviceMeta = WbDeviceMeta(json.get("meta", JsonDict()))


class HikvisionCameraEvent:
    def __init__(self, json: JsonDict):
        event_data: JsonDict = json.get("EventNotificationAlert", json)

        self.type: str = event_data.get("eventType")
        self.state: str = event_data.get("eventState")

    def get_state_to_int(self) -> int | None:
        if self.state != "active" and self.state != "inactive":
            return None
        return 1 if self.state == "active" else 0

    def __str__(self):
        return (f'CameraEvent('
                f'type={self.type}, '
                f'state={self.state}'
                f')')
