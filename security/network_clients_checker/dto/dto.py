from datetime import datetime

from common.utils import JsonDict
from keenetic.dto.dto import NetworkClient, ClientStatus
from mqtt.dto.dto import MQTTDeviceConfig
from security.network_clients_checker.utils.utils import get_client_status


class ClientCheckerConfig:
    def __init__(self, json: JsonDict):
        self.pool_interval = json.get("poolInterval", 15)
        self.mqtt = MQTTDeviceConfig(json.get("mqtt"))


class ClientConnectionInfo:
    def __init__(self, client: NetworkClient, status: ClientStatus = None):
        self.client = client
        self.status = status if status is not None else get_client_status(client)

    def __str__(self):
        return (f'ClientConnectionInfo('
                f'client={self.client}, '
                f'status={self.status}'
                f')')

    def __eq__(self, __value):
        if not __value or not isinstance(__value, ClientConnectionInfo):
            return False
        return self.client.__eq__(__value.client)

    def __hash__(self):
        return hash(self.client)


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


class ClientsCheckerLastState:
    def __init__(
            self,
            online: set[ClientConnectionInfo] = None,
            trusted_online: set[ClientConnectionInfo] = None,
            unregistered_online: set[ClientConnectionInfo] = None,
    ):
        self.online = online if online else set()
        self.trusted_online = trusted_online if online else set()
        self.unregistered_online = unregistered_online if unregistered_online else set()
