from enum import Enum

from common.utils import JsonDict


class KeeneticRouterConfig:
    def __init__(self, json: JsonDict):
        self.host = json.get("host")
        self.username: str = json.get("username")
        self.password: str = json.get("password")


class ClientStatus(Enum):
    PENDING = 0
    ONLINE = 1
    OFFLINE = 2


class NetworkClient:
    def __init__(self, json: JsonDict):
        self.name = json.get("name")
        self.mac = json.get("mac")
        self.address = json.get("ip")
        self.registered = json.get("registered")
        self.active = json.get("active")

    def __str__(self):
        return (f"NetworkClient("
                f"name={self.name}, "
                f"ip={self.address}, "
                f"mac={self.mac}, "
                f"registered={self.registered}, "
                f"active={self.active}"
                f")"
                )
