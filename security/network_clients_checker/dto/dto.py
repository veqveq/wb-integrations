from typing import Any

from common.utils import JsonDict
from mqtt.dto.dto import MQTTDeviceConfig
from datetime import datetime

from keenetic.dto.dto import NetworkClient, ClientStatus
from security.network_clients_checker.utils.utils import get_client_status


class ClientCheckerConfig:
    def __init__(self, json: JsonDict):
        self.pool_interval = json.get("poolInterval", 15)
        self.mqtt = MQTTDeviceConfig(json.get("mqtt"))


class ClientConnectionInfo:
    def __init__(self,
                 client: NetworkClient,
                 status: ClientStatus = None,
                 last_change_status_ts: datetime = datetime.now()
                 ):
        self.client = client
        self.status = status if status is not None else get_client_status(client)
        self.last_change_status_ts = last_change_status_ts

    def __str__(self):
        return (f'ClientConnectionInfo('
                f'client={self.client}, '
                f'status={self.status}'
                f')')


class UnregisteredClientInfo:
    def __init__(self, client: NetworkClient):
        if client.registered is True:
            raise AttributeError(f'Client: {client} is registered!')
        self.name = client.name
        self.mac = client.mac
        self.ip = client.address
        self.timestamp = datetime.now()

    def __str__(self):
        return (f'UnregisteredClientInfo('
                f'name={self.name}, '
                f'mac={self.mac}, '
                f'ip={self.ip}'
                f')')


