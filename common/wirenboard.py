from typing import Any

from common.utils import JsonDict


def prepare_meta_field_value(value: Any) -> str | None:
    if value is None:
        return value
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


class WbDeviceControlMeta:
    def __init__(self, json: JsonDict):
        self.type: str = json["type"]
        self.name: str = json.get("name")
        self.readonly: bool = json.get("readonly")
        self.order: int = json.get("order")

    def get_meta(self) -> JsonDict:
        return JsonDict({fld_name: prepare_meta_field_value(fld_value) for fld_name, fld_value in vars(self).items()})


class WbDeviceMeta:
    excluded_from_meta_fields: list[str] = ["deviceName", "controls"]

    def __init__(self, json: JsonDict):
        self.deviceName: str = json["deviceName"]
        self.name: str = json.get("name")
        self.controls: dict[str, WbDeviceControlMeta] = {
            name: WbDeviceControlMeta(control) for name, control in json.get("controls", {}).items()
        }

    def get_meta(self) -> JsonDict:
        return JsonDict(
            {fld_name: prepare_meta_field_value(fld_value) for fld_name, fld_value in vars(self).items()
             if fld_name not in WbDeviceMeta.excluded_from_meta_fields}
        )
