import time

from common.config_loader import load_config_json
from common.logger import configure_logger
from common.utils import BASE_PATH
from keenetic.dto.dto import ClientStatus
from keenetic.service.keenetic_router import KeeneticRouter, NetworkClient
from mqtt.service.mqtt import MQTTPublisher
from security.network_clients_checker.dto.dto import ClientConnectionInfo, ClientCheckerConfig, UnregisteredClientInfo
from security.network_clients_checker.utils.utils import get_client_status

PATH = BASE_PATH / "security/network_clients_checker"
LOG_PATH = PATH / "logs"
CONFIG_PATH = PATH / "config"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
TRUSTED_CLIENTS_FILE = CONFIG_PATH / "trusted_network_clients.json"

LOGGER = configure_logger("NETWORK_CLIENTS", LOG_PATH)


class NetworkClientsChecker:
    def __init__(self):
        self.settings = ClientCheckerConfig(load_config_json(SETTINGS_FILE))
        self.trusted_clients = load_config_json(TRUSTED_CLIENTS_FILE)
        self.clients_map: dict[str, ClientConnectionInfo] = {}
        self.mqtt_publisher = MQTTPublisher()
        self.has_trusted_online = False

    def close(self):
        self.mqtt_publisher.publish(
            self.settings.mqtt.device_name,
            self.settings.mqtt.controls["status"],
            0
        )
        self.mqtt_publisher.disconnect()

    def update_clients_statuses(self, network_clients: list[NetworkClient]):
        if network_clients is None:
            return
        for client in network_clients:
            if self.clients_map.get(client.mac) is None:
                self.clients_map[client.mac] = ClientConnectionInfo(client)
                continue
            connection_info: ClientConnectionInfo = self.clients_map[client.mac]

            saved_status = connection_info.status
            received_status = get_client_status(client)
            new_status = None

            if saved_status == ClientStatus.PENDING:
                new_status = received_status
            elif saved_status != received_status:
                if received_status == ClientStatus.ONLINE:
                    new_status = received_status
                else:
                    new_status = ClientStatus.PENDING

            if new_status is not None:
                self.clients_map[client.mac] = ClientConnectionInfo(client, new_status)

    def check_unregistered(self, network_clients: list[NetworkClient]) -> int:
        if network_clients is None:
            return 0
        new_unregistered_clients = [UnregisteredClientInfo(client) for client in network_clients
                                    if client.registered is False
                                    and self.clients_map.get(client.mac) is None
                                    ]
        if len(new_unregistered_clients) > 0:
            LOGGER.info(f"Found new unregistered network clients: {[f'{uc}; ' for uc in new_unregistered_clients]}")
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["unregisteredClients"],
                [client.name for client in new_unregistered_clients]
            )
        return len(new_unregistered_clients)

    def check_trusted(self, network_clients: list[NetworkClient]) -> tuple[int, int]:
        if network_clients is None:
            return 0, 0

        trusted_clients = self._get_trusted_clients_info(network_clients)
        connected, disconnected = self._group_clients_info_by_activity_status(trusted_clients)

        self.mqtt_publisher.publish(
            self.settings.mqtt.device_name,
            self.settings.mqtt.controls["hasConnectedTrusted"],
            1 if len(connected) > 0 else 0
        )

        if len(connected) > 0:
            LOGGER.info(f"Found trusted network clients: {[f'{uc}; ' for uc in connected]}")
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["connectedTrusted"],
                str([client_info.client.name for client_info in connected])
            )
            self._check_new_connections(connected)

        self.has_trusted_online = len(connected) > 0

        if len(disconnected) > 0:
            self._check_new_disconnections(disconnected)
        return len(connected), len(disconnected)

    def _get_trusted_clients_info(self, clients_list: list[NetworkClient]) -> list[ClientConnectionInfo]:
        if clients_list is None:
            return []
        return [
            ClientConnectionInfo(client) for client in clients_list if client.mac in self.trusted_clients.keys()
        ]

    @staticmethod
    def _group_clients_info_by_activity_status(
            clients_info_list: list[ClientConnectionInfo | NetworkClient]
    ) -> tuple[list[ClientConnectionInfo | NetworkClient], list[ClientConnectionInfo | NetworkClient]]:
        if clients_info_list is None:
            return [], []

        result: dict[bool, list] = {True: [], False: []}
        for connection_info in clients_info_list:
            if isinstance(connection_info, ClientConnectionInfo):
                client = connection_info.client
            elif isinstance(connection_info, NetworkClient):
                client = connection_info
            else:
                LOGGER.warning(
                    f"Group clients info by activity status allowed only ClientConnectionInfo or NetworkClient. "
                    f"Received: {connection_info.__class__}")
                continue
            result[client.active].append(connection_info)
        return result[True], result[False]

    def _check_new_connections(self, connections_info: list[ClientConnectionInfo]):
        if connections_info is None:
            return

        new_connected_trusted_clients = [
            connection_info for connection_info in connections_info
            if (self.clients_map.get(connection_info.client.mac) is None or
                self.clients_map.get(connection_info.client.mac).status == ClientStatus.OFFLINE)
        ]

        if len(new_connected_trusted_clients) > 0:
            LOGGER.info(f"Found new trusted network clients: {[f'{uc}; ' for uc in new_connected_trusted_clients]}")
            if self.has_trusted_online is False:
                self.mqtt_publisher.publish(
                    self.settings.mqtt.device_name,
                    self.settings.mqtt.controls["lastTrusted"],
                    new_connected_trusted_clients[0].client.name
                )
                self.mqtt_publisher.publish(
                    self.settings.mqtt.device_name,
                    self.settings.mqtt.controls["lastTrustedTs"],
                    str(new_connected_trusted_clients[0].last_change_status_ts)
                )
                self.has_trusted_online = True

    def _check_new_disconnections(self, disconnections_info: list[ClientConnectionInfo]):
        if disconnections_info is None:
            return

        new_disconnected = [
            connection_info for connection_info in disconnections_info
            if (
                    connection_info.status == ClientStatus.OFFLINE
                    and self.clients_map.get(connection_info.client.mac) is not None
                    and self.clients_map.get(connection_info.client.mac).status == ClientStatus.PENDING
            )
        ]
        if len(new_disconnected) > 0 and self.has_trusted_online is False:
            LOGGER.info(f"Found trusted network clients disconnected: {[f'{uc}; ' for uc in new_disconnected]}")
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["lastTrusted"],
                new_disconnected[-1].client.name
            )
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["lastTrustedTs"],
                new_disconnected[-1].last_change_status_ts
            )


if __name__ == '__main__':
    router = None
    clients_checker = None

    try:
        router = KeeneticRouter()
        clients_checker = NetworkClientsChecker()
        pool_interval = clients_checker.settings.pool_interval
        LOGGER.info("Get started")
        clients_checker.mqtt_publisher.publish(
            clients_checker.settings.mqtt.device_name,
            clients_checker.settings.mqtt.controls["status"],
            1
        )
        while True:
            try:
                clients: list[NetworkClient] = router.get_clients()
                LOGGER.debug(f"Received clients: {[str(c) for c in clients]}")
                unregistered_count: int = clients_checker.check_unregistered(clients)
                online, offline = clients_checker.check_trusted(clients)
                clients_checker.update_clients_statuses(clients)
                LOGGER.info(
                    f"Clients handled. "
                    f"Received: {len(clients)}, "
                    f"unregistered: {unregistered_count}, "
                    f"trusted online: {online}, "
                    f"trusted offline: {offline}. "
                    f"Wait {pool_interval} sec..."
                )
                time.sleep(pool_interval)
            except Exception:
                LOGGER.error("Handle clients receiving error", exc_info=True)
                time.sleep(5)
    except Exception as e:
        LOGGER.error("NetworkClientChecker exception", exc_info=True)
        raise e
    finally:
        if clients_checker is not None:
            clients_checker.close()
        if router is not None:
            router.close()
        LOGGER.info("Finished")
