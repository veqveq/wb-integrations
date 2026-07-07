import time

from common.config import load_config_json, get_service_and_config_paths
from common.logger import configure_logger
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
        self.settings = ClientCheckerConfig(load_config_json(SETTINGS_FILE))
        self.trusted_clients = load_config_json(TRUSTED_CLIENTS_FILE)
        self.last_state = ClientsCheckerLastState()
        self.mqtt_publisher = MQTTPublisher()
        self._send_status(1)

    def close(self):
        self._send_status(0)
        self.mqtt_publisher.disconnect()

    def _send_status(self, status: int):
        self.mqtt_publisher.publish(
            self.settings.mqtt.device_name,
            self.settings.mqtt.controls["status"],
            status
        )

    def get_client_connection_info(self, network_client: NetworkClient) -> ClientConnectionInfo:
        client_last_state_list = [last for last in self.last_state.online if last.client.mac == network_client.mac]
        if not client_last_state_list:
            return ClientConnectionInfo(network_client)
        client_last_state = client_last_state_list[0]
        if client_last_state.status == ClientStatus.PENDING:
            return (ClientConnectionInfo(network_client)
                    if network_client.active
                    else ClientConnectionInfo(network_client, ClientStatus.OFFLINE))
        return client_last_state

    def check_clients_online_update(self, network_clients: list[ClientConnectionInfo]) -> set[ClientConnectionInfo]:
        online_clients_info: set[ClientConnectionInfo] = set(
            [info for info in network_clients if info and info.status != ClientStatus.OFFLINE]
        )
        if len(self.last_state.online) != len(online_clients_info):
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["clientsOnlineCount"],
                len(online_clients_info)
            )

        if online_clients_info != self.last_state.online:
            connected = online_clients_info - self.last_state.online
            disconnected = self.last_state.online - online_clients_info
            LOGGER.info(
                f"New clients connected: {[str(info.client.name) for info in connected]}"
            ) if connected else None
            LOGGER.info(
                f"Clients disconnected: {[str(info.client.name) for info in disconnected]}"
            ) if disconnected else None
        self.last_state.online = online_clients_info
        return online_clients_info

    def check_trusted_clients_online_update(self, online_clients: set[ClientConnectionInfo]):
        trusted_online_dict: dict[str: ClientConnectionInfo] = ({
            info.client.mac: info for info in online_clients
            if info.client.mac in self.trusted_clients.keys()
               and info.status != ClientStatus.OFFLINE
        })
        if trusted_online_dict:
            for mac, info in trusted_online_dict.items():
                trusted_client_name = self.trusted_clients.get(mac)["name"]
                info.client.name = trusted_client_name

        trusted_online: set[ClientConnectionInfo] = (
            set(trusted_online_dict.values())
            if trusted_online_dict
            else set()
        )

        if trusted_online != self.last_state.trusted_online:
            connected = trusted_online - self.last_state.trusted_online
            disconnected = self.last_state.trusted_online - trusted_online
            LOGGER.info(
                f"New trusted clients connected: {[info.client.name for info in connected]}"
            ) if connected else None
            LOGGER.info(
                f"Trusted clients disconnected: {[info.client.name for info in disconnected]}"
            ) if disconnected else None

            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["trustedClientsOnline"],
                str([info.client.name for info in trusted_online])
            )

        self.last_state.trusted_online = trusted_online

    def check_unregistered_clients_online_update(self, online_clients: set[ClientConnectionInfo]):
        unregistered_online: set[ClientConnectionInfo] = set([
            info for info in online_clients
            if info.status != ClientStatus.OFFLINE
               and info.client.registered is False
        ])

        if unregistered_online != self.last_state.unregistered_online:
            connected = unregistered_online - self.last_state.unregistered_online
            disconnected = self.last_state.unregistered_online - unregistered_online
            LOGGER.info(f"New clients connected: {[info.client.name for info in connected]}") if connected else None
            LOGGER.info(
                f"Clients disconnected: {[info.client.name for info in disconnected]}") if disconnected else None
            self.mqtt_publisher.publish(
                self.settings.mqtt.device_name,
                self.settings.mqtt.controls["unregisteredClientsOnline"],
                str([info.client.name for info in unregistered_online])
            )
        self.last_state.unregistered_online = unregistered_online


if __name__ == '__main__':
    router = None
    clients_checker = None

    try:
        router = KeeneticRouter()
        clients_checker = NetworkClientsChecker()
        pool_interval = clients_checker.settings.pool_interval
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

                online_clients: set[ClientConnectionInfo] = clients_checker.check_clients_online_update(network_clients)
                clients_checker.check_trusted_clients_online_update(online_clients)
                clients_checker.check_unregistered_clients_online_update(online_clients)
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
