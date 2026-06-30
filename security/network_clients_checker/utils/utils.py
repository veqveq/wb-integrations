from keenetic.dto.dto import NetworkClient, ClientStatus


def get_client_status(client: NetworkClient):
    return ClientStatus.ONLINE if client.active else ClientStatus.OFFLINE
