import time

from common.config import load_config_json, get_service_and_config_paths
from common.logger import configure_logger
from common.utils import JsonDict
from common.wirenboard import WbDeviceMeta
from keenetic.dto.dto import ClientStatus
from keenetic.service.keenetic_router import KeeneticRouter, NetworkClient
from mqtt.service.mqtt import MQTTPublisher
from security.network_clients_checker.dto.dto import (
    ClientCheckerConfig,
    ClientsCheckerLastState,
    ClientConnectionInfo
)

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("security/network_clients_checker")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
TRUSTED_CLIENTS_FILE = CONFIG_PATH / "trusted_network_clients.json"

LOGGER = configure_logger("logs", LOG_PATH)


class NetworkClientsChecker:
    def __init__(self):
        settings = ClientCheckerConfig(load_config_json(SETTINGS_FILE))

        self.pool_interval: int = settings.pool_interval
        self.meta: WbDeviceMeta = settings.meta

        self.trusted_clients: JsonDict = load_config_json(TRUSTED_CLIENTS_FILE)
        self.last_state: ClientsCheckerLastState = ClientsCheckerLastState()
        self.mqtt_publisher: MQTTPublisher = MQTTPublisher()

        self.mqtt_publisher.publish_meta(self.meta)
        self._send_status(1)

    def close(self):
        self._send_status(0)
        self.mqtt_publisher.disconnect()

    def _send_status(self, status: int):
        self.mqtt_publisher.safe_publish(self.meta, "status", status)

    def get_client_connection_info(self, network_client: NetworkClient) -> ClientConnectionInfo:
        client_last_state_list: list[ClientConnectionInfo] = (
            [last for last in self.last_state.online if last.client.mac == network_client.mac]
            if self.last_state.online else None
        )
        if not client_last_state_list:
            return ClientConnectionInfo(network_client)

        client_last_state: ClientConnectionInfo = client_last_state_list[0]

        if client_last_state.status == ClientStatus.PENDING and not network_client.active:
            return ClientConnectionInfo(network_client, ClientStatus.OFFLINE)

        return ClientConnectionInfo(network_client)

    def get_clients_online(self, network_clients: list[ClientConnectionInfo]) -> set[ClientConnectionInfo]:
        online_clients: set[ClientConnectionInfo] = set(
            [info for info in network_clients if info and info.status != ClientStatus.OFFLINE]
        )
        if self.last_state.online is None:
            self.mqtt_publisher.safe_publish(self.meta, "clientsOnlineCount", str(len(online_clients)))
            self._log_connections_changes(self.last_state.online, online_clients)
            self.last_state.online = online_clients
            return online_clients

        if len(self.last_state.online) != len(online_clients):
            self.mqtt_publisher.safe_publish(self.meta, "clientsOnlineCount", str(len(online_clients)))

        if online_clients != self.last_state.online:
            self._log_connections_changes(self.last_state.online, online_clients)

        self.last_state.online = online_clients
        return online_clients

    def update_trusted_clients_online(self, online_clients: set[ClientConnectionInfo]):
        trusted_online_dict: dict[str: ClientConnectionInfo] = ({
            info.client.mac: info for info in online_clients
            if info.client.mac in self.trusted_clients.keys()
               and info.status != ClientStatus.OFFLINE
        })
        if trusted_online_dict:
            for mac, info in trusted_online_dict.items():
                trusted_client_name: str = self.trusted_clients.get(mac)["name"]
                info.client.name = trusted_client_name

        trusted_online: set[ClientConnectionInfo] = (
            set(trusted_online_dict.values())
            if trusted_online_dict else set()
        )

        if self.last_state.trusted_online is None or trusted_online != self.last_state.trusted_online:
            self.mqtt_publisher.safe_publish(
                self.meta,
                "trustedClientsOnline",
                ",".join([info.client.name for info in trusted_online]) if len(trusted_online) > 0 else " "
            )
            self._log_connections_changes(self.last_state.trusted_online, trusted_online, "trusted")

        self.last_state.trusted_online = trusted_online

    def update_unregistered_clients_online(self, online_clients: set[ClientConnectionInfo]):
        unregistered_online: set[ClientConnectionInfo] = set([
            info for info in online_clients
            if info.status != ClientStatus.OFFLINE
               and info.client.registered is False
        ])

        if self.last_state.unregistered_online is None or unregistered_online != self.last_state.unregistered_online:
            self.mqtt_publisher.safe_publish(
                self.meta,
                "unregisteredClientsOnline",
                ",".join([info.client.name for info in unregistered_online]) if len(unregistered_online) > 0 else " "
            )
            self._log_connections_changes(
                self.last_state.unregistered_online, unregistered_online, "unregistered"
            )
        self.last_state.unregistered_online = unregistered_online

    @staticmethod
    def _log_connections_changes(
            last_connections: set[ClientConnectionInfo] | None,
            current_connections: set[ClientConnectionInfo] | None,
            connections_list_title: str = ""
    ):
        current_connections: set = current_connections or set()
        last_connections: set = last_connections or set()
        connected: set[ClientConnectionInfo] = current_connections - last_connections
        disconnected: set[ClientConnectionInfo] = last_connections - current_connections
        LOGGER.info(
            f"New {connections_list_title} clients connected: {[info.client.name for info in connected]}"
        ) if connected else None
        LOGGER.info(
            f"Current {connections_list_title} clients disconnected: {[info.client.name for info in disconnected]}"
        ) if disconnected else None


if __name__ == '__main__':
    router = None
    clients_checker = None

    try:
        router = KeeneticRouter()
        clients_checker = NetworkClientsChecker()
        pool_interval = clients_checker.pool_interval
        LOGGER.info("Get started")

        while True:
            try:
                network_clients: list[ClientConnectionInfo] = [
                    clients_checker.get_client_connection_info(client) for client in router.get_clients()
                ]
                if network_clients:
                    LOGGER.debug(f"Received clients: {[str(c) for c in network_clients]}")
                else:
                    LOGGER.warning("Info about router clients not received")
                    continue

                clients_online: set[ClientConnectionInfo] = clients_checker.get_clients_online(network_clients)
                clients_checker.update_trusted_clients_online(clients_online)
                clients_checker.update_unregistered_clients_online(clients_online)
                time.sleep(pool_interval)
            except Exception:
                LOGGER.error("Handle clients receiving error", exc_info=True)
                time.sleep(5)
    except Exception as e:
        LOGGER.error("NetworkClientChecker exception", exc_info=True)
        raise e
    finally:
        clients_checker.close() if clients_checker else None
        router.close() if router else None
        LOGGER.info("Finished")
