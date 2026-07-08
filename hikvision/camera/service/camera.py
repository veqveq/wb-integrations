from typing import AsyncIterator

import xmltodict
from httpx import AsyncClient, DigestAuth, Response

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from common.utils import JsonDict
from hikvision.camera.dto.dto import HikvisionCameraConfig, HikvisionCameraAlert

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("hikvision/camera")
LOG_PATH = SERVICE_PATH / "logs"
ENDPOINTS_FILE = CONFIG_PATH / "endpoints.json"


class HikvisionCamera:
    def __init__(self, config: HikvisionCameraConfig):
        self.name = config.name
        endpoints: JsonDict = load_config_json(ENDPOINTS_FILE)
        self.endpoints = {k: f"http://{config.host}{v}" for k, v in endpoints.items()}
        self.session: AsyncClient = AsyncClient(auth=DigestAuth(config.username, config.password), timeout=60)
        self.logger = configure_logger(config.meta.deviceName, LOG_PATH)
        self.meta = config.meta

    async def listen_events_stream(self):
        async with self.session.stream("GET", self.endpoints["getEventsStream"]) as connection:
            connection.raise_for_status()
            self.logger.info(f'Connected to {self.endpoints["getEventsStream"]}')
            buffer = bytearray()
            start_tag = b"<EventNotificationAlert"
            end_tag = b"</EventNotificationAlert>"
            async for chunk in connection.aiter_bytes():
                buffer += chunk
                while True:
                    end = buffer.find(end_tag)
                    if end == -1:
                        break
                    end += len(end_tag)
                    raw = bytes(buffer[:end])
                    del buffer[:end]
                    start = raw.find(start_tag)
                    if start == -1:
                        continue
                    xml = raw[start:].decode("utf-8")
                    yield self._process_xml(xml)

    async def close(self):
        await self.session.aclose()
        self.logger.info("Connection closed...")

    async def _connect_to_api(self, resource_path: str) -> AsyncIterator[Response]:

        async with self.session.stream("GET", resource_path) as connection:
            try:
                connection.raise_for_status()
                self.logger.info(f'Connected to {resource_path}')
                return connection
            except Exception:
                self.logger.error(f'Connection error. Path: {resource_path}', exc_info=True)

    def _process_xml(self, xml: str) -> HikvisionCameraAlert:
        try:
            json: JsonDict = xmltodict.parse(xml)
            return HikvisionCameraAlert(json)
        except Exception:
            self.logger.error(f"Parse XML error: xml={xml}", exc_info=True)
