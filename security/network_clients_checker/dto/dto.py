from common.utils import JsonDict
from common.wirenboard import WbDeviceMeta
from keenetic.dto.dto import NetworkClient, ClientStatus
from security.network_clients_checker.utils.utils import get_client_status


class ClientCheckerConfig:
    def __init__(self, json: JsonDict):
        self.pool_interval: int = json.get("poolInterval", 15)
        self.meta: WbDeviceMeta = WbDeviceMeta(json.get("meta"))


class ClientConnectionInfo:
    def __init__(self, client: NetworkClient, status: ClientStatus = None):
        self.client: NetworkClient = client
        self.status: ClientStatus = status if status is not None else get_client_status(client)

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


class ClientsCheckerLastState:
    def __init__(
            self,
            online: set[ClientConnectionInfo] = None,
            trusted_online: set[ClientConnectionInfo] = None,
            unregistered_online: set[ClientConnectionInfo] = None,
    ):
        self.online: set[ClientConnectionInfo] = online
        self.trusted_online: set[ClientConnectionInfo] = trusted_online
        self.unregistered_online: set[ClientConnectionInfo] = unregistered_online
