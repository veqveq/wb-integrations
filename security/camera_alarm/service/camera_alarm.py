import asyncio
from pathlib import Path

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from hikvision.camera.dto.dto import HikvisionCameraConfig, HikvisionCameraEvent
from hikvision.camera.service.camera import HikvisionCamera
from mqtt.service.mqtt import MQTTPublisher
from security.camera_alarm.dto.dto import CameraAlarmSettings, CameraAlarmEventType, CameraAlarmEvent

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("security/camera_alarm")

LOG_PATH: Path = SERVICE_PATH / "logs"
SETTINGS_FILE: Path = CONFIG_PATH / "settings.json"
CAMERAS_FILE: Path = CONFIG_PATH / "cameras.json"

LOGGER = configure_logger("logs", LOG_PATH)


class HikvisionCameraAlarmService:
    def __init__(self, camera_config: HikvisionCameraConfig):
        settings: CameraAlarmSettings = CameraAlarmSettings(load_config_json(SETTINGS_FILE))

        self.camera: HikvisionCamera = HikvisionCamera(camera_config)
        self.mqtt: MQTTPublisher = MQTTPublisher()
        self.reconnected_delay: int = settings.reconnected_delay_sec
        self.handled_events: dict[CameraAlarmEventType, CameraAlarmEvent] = settings.events
        self.event_states: dict[str, bool] = {str(event.value): False for event in self.handled_events.keys()}
        self.vmd_counter: int = 0
        self.vmd_timer: asyncio.Task | None = None

        self.mqtt.publish_meta(self.camera.meta)

    async def handle_alarm_events(self):
        try:
            while True:
                try:
                    self.mqtt.safe_publish(self.camera.meta, "streamConnected", 1)
                    LOGGER.info(f'Camera "{self.camera.name}". Listen alarm events started...')
                    async for event in self.camera.listen_events_stream():
                        event_type: CameraAlarmEventType = CameraAlarmEventType.from_string(event.type)
                        if event_type not in self.handled_events.keys():
                            continue
                        self._handle_alarm_event(event)
                except Exception:
                    LOGGER.error(f'Camera "{self.camera.name}". Handle alarm event error', exc_info=True)
                finally:
                    self.mqtt.safe_publish(self.camera.meta, "streamConnected", 0)
                    LOGGER.info(
                        f'Camera "{self.camera.name}". Listen alarm events stopped. '
                        f'Reconnect after {self.reconnected_delay} sec'
                    )
                    await asyncio.sleep(self.reconnected_delay)
        finally:
            await self.camera.close()
            self.mqtt.safe_publish(self.camera.meta, "streamConnected", 0)
            self.mqtt.disconnect()

    def _handle_alarm_event(self, event: HikvisionCameraEvent):
        event_type: CameraAlarmEventType = CameraAlarmEventType.from_string(event.type)
        if event_type == CameraAlarmEventType.VMD:
            self._handle_vmd_event(event)
        elif event_type == CameraAlarmEventType.UNKNOWN:
            LOGGER.warning(f"Unhandled Camera alarm event: {event}. Camera: {self.camera.name}")
        else:
            self._handle_smart_event(event)

    def _handle_vmd_event(self, event: HikvisionCameraEvent):
        if CameraAlarmEventType.from_string(event.type) != CameraAlarmEventType.VMD:
            return
        if event.get_state_to_int() == 0:
            return
        self._restart_vmd_inactive_timer()
        self.vmd_counter += 1
        if self.event_states.get(event.type):
            return
        if self.vmd_counter >= self.handled_events[CameraAlarmEventType.VMD].params["requiredActiveCount"]:
            self.event_states[event.type] = event.get_state_to_int() == 1
            self.mqtt.safe_publish(
                self.camera.meta,
                self.handled_events.get(CameraAlarmEventType.VMD).control,
                1
            )
            LOGGER.info(f'Camera "{self.camera.name}", event: VMD, state: ON')

    def _handle_smart_event(self, event: HikvisionCameraEvent):
        current_state: bool = self.event_states.get(event.type)
        if event.state == current_state:
            return
        self.event_states[event.type]: bool = bool(event.get_state_to_int())
        self.mqtt.safe_publish(
            self.camera.meta,
            self.handled_events.get(CameraAlarmEventType.from_string(event.type)).control,
            event.get_state_to_int()
        )
        LOGGER.info(
            f'Camera "{self.camera.name}", '
            f'event: {event.type}, '
            f'state: {"ON" if event.get_state_to_int() == 1 else "OFF"}'
        )

    async def _inactive_vmd_timeout(self):
        await asyncio.sleep(self.handled_events[CameraAlarmEventType.VMD].params.get("activeExpirationSec", 2))
        self.vmd_counter = 0
        self.mqtt.safe_publish(
            self.camera.meta,
            self.handled_events.get(CameraAlarmEventType.VMD).control,
            0
        )
        self.event_states[str(CameraAlarmEventType.VMD.value)] = False
        LOGGER.info(f'Camera "{self.camera.name}", event: VMD, state: OFF')

    def _restart_vmd_inactive_timer(self):
        if self.vmd_timer:
            self.vmd_timer.cancel()

        self.vmd_timer = asyncio.create_task(self._inactive_vmd_timeout())


async def main():
    camera_configs: list[HikvisionCameraConfig] = [
        HikvisionCameraConfig(config) for config in load_config_json(CAMERAS_FILE)
    ]
    services: list[HikvisionCameraAlarmService] = [HikvisionCameraAlarmService(config) for config in camera_configs]
    await asyncio.gather(*(service.handle_alarm_events() for service in services))


if __name__ == '__main__':
    asyncio.run(main())
