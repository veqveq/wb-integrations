from collections.abc import AsyncIterable
from logging import Logger
from typing import AsyncIterator
import datetime

import xmltodict
from httpx import AsyncClient, DigestAuth, Response

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from common.utils import JsonDict
from common.wirenboard import WbDeviceMeta
from hikvision.camera.dto.dto import HikvisionCameraConfig, HikvisionCameraEvent

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("hikvision/camera")
LOG_PATH = SERVICE_PATH / "logs"
ENDPOINTS_FILE = CONFIG_PATH / "endpoints.json"


class HikvisionCamera:
    def __init__(self, config: HikvisionCameraConfig):
        endpoints: JsonDict = load_config_json(ENDPOINTS_FILE)

        self.name = config.name
        self.endpoints: dict[str, str] = {k: f"http://{config.host}{v}" for k, v in endpoints.items()}
        self.session: AsyncClient = AsyncClient(auth=DigestAuth(config.username, config.password), timeout=60)
        self.logger: Logger = configure_logger(config.meta.deviceName, LOG_PATH)
        self.meta: WbDeviceMeta = config.meta

    async def listen_events_stream(self) -> AsyncIterable[HikvisionCameraEvent]:
        async with self.session.stream("GET", self.endpoints["getEventsStream"]) as connection:
            connection.raise_for_status()
            self.logger.info(f'Connected to {self.endpoints["getEventsStream"]}')

            buffer: bytearray = bytearray()
            start_tag: bytes = b"<EventNotificationAlert"
            end_tag: bytes = b"</EventNotificationAlert>"

            async for chunk in connection.aiter_bytes():
                buffer += chunk
                while True:
                    end: int = buffer.find(end_tag)
                    if end == -1:
                        break
                    end += len(end_tag)

                    raw: bytes = bytes(buffer[:end])
                    del buffer[:end]
                    start: int = raw.find(start_tag)
                    if start == -1:
                        continue
                    xml: str = raw[start:].decode("utf-8")
                    yield self._process_xml(xml)

    async def close(self):
        await self.session.aclose()
        self.logger.info("Connection closed...")

    async def get_snapshot(self) -> bytes:
        response: Response = await self.session.get(self.endpoints["getSnapshot"])
        response.raise_for_status()
        self.logger.debug(
            f"Get snapshot from {self.name} "
            f"at {datetime.datetime.now()}. "
            f"Size: {round(len(response.content) / 1024, 0)} kB"
        )
        return response.content

    def _process_xml(self, xml: str) -> HikvisionCameraEvent:
        try:
            json: JsonDict = xmltodict.parse(xml)
            return HikvisionCameraEvent(json)
        except Exception:
            self.logger.error(f"Parse XML error: xml={xml}", exc_info=True)
