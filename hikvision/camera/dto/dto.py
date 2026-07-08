from common.utils import JsonDict
from common.wirenboard import WbDeviceMeta


class HikvisionCameraConfig:
    UNKNOWN_CAMERA_COUNTER: int = 0

    @staticmethod
    def get_unknown_camera_name() -> str:
        HikvisionCameraConfig.UNKNOWN_CAMERA_COUNTER += 1
        return f"Камера {HikvisionCameraConfig.UNKNOWN_CAMERA_COUNTER}"

    def __init__(self, json: JsonDict):
        self.name = json.get("name", HikvisionCameraConfig.get_unknown_camera_name())
        self.host = json.get("host")
        self.username = json.get("username")
        self.password = json.get("password")
        self.meta = WbDeviceMeta(json.get("meta"))


class HikvisionCameraAlert:
    def __init__(self, json: JsonDict):
        event_data = json.get("EventNotificationAlert", json)
        self.timestamp = event_data.get("dateTime")
        self.type = event_data.get("eventType")
        self.state = event_data.get("eventState")
        self.description = event_data.get("description", None)

    def get_state_to_int(self) -> int | None:
        if self.state != "active" and self.state != "inactive":
            return None
        return 1 if self.state == "active" else 0

    def __str__(self):
        return (f'CameraEvent('
                f'type={self.type}, '
                f'state={self.state}, '
                f'description={self.description}, '
                f'timestamp={self.timestamp}'
                f')')
