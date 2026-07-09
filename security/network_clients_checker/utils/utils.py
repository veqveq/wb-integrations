from keenetic.dto.dto import NetworkClient, ClientStatus


def get_client_status(client: NetworkClient) -> ClientStatus:
    return ClientStatus.ONLINE if client.active else ClientStatus.OFFLINE
