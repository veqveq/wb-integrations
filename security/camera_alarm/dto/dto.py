from enum import StrEnum

from common.utils import JsonDict


class CameraAlarmEventType(StrEnum):
    VMD = "VMD",
    FIELD_INTRUSION = "fielddetection"
    LINE_CROSSING = "linedetection"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "CameraAlarmEventType":
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


class CameraAlarmEvent:
    def __init__(self, json: JsonDict):
        self.type: str = CameraAlarmEventType.from_string(json["name"])
        self.control: str = json["control"]
        self.params: JsonDict = json.get("params", JsonDict())


class CameraAlarmSettings:
    def __init__(self, json: JsonDict):
        self.reconnected_delay_sec: int = json.get("reconnectDelaySec", 5)
        self.events: dict[CameraAlarmEventType, CameraAlarmEvent] = {
            CameraAlarmEventType.from_string(event["name"]): CameraAlarmEvent(event) for event in json.get("events")
        }
