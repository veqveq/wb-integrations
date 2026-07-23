from typing import Any

from paho.mqtt.client import Client

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from common.wirenboard import WbDeviceMeta, WbDeviceControlMeta
from mqtt.dto.dto import MQTTConfig

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("mqtt")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"

LOGGER = configure_logger("logs", LOG_PATH)


class MQTTPublisher:
    def __init__(self):
        try:
            config: MQTTConfig = MQTTConfig(load_config_json(SETTINGS_FILE))

            self.client: Client = Client(client_id=config.client_id)
            self.client.connect(config.host, config.port, keepalive=60)
            self.client.loop_start()
            LOGGER.info("MQTT connected")
        except Exception:
            LOGGER.error("MQTT connect error: ", exc_info=True)

    def safe_publish(self, device_meta: WbDeviceMeta, control: str, value: Any, retain: bool = True):
        if not device_meta.deviceName:
            AttributeError(f"Publish error. Device name required: {device_meta}")
        if control not in device_meta.controls.keys():
            ChildProcessError(f"Publish error. Control {control} not defined in meta: {device_meta}")
        self._unsafe_publish(device_meta.deviceName, control, value, retain)

    def publish_meta(self, meta: WbDeviceMeta):
        if not meta:
            return
        device_name: str = meta.deviceName
        if not device_name:
            AttributeError(f"Publish meta error. Device name required: {meta}")
        self._send_device_meta(meta)

        for control_name, control_meta in meta.controls.items():
            if not control_name:
                AttributeError(f"Publish meta error. Device: {device_name}. Control name required: {control_meta}")
            self._send_control_meta(device_name, control_name, control_meta)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        LOGGER.info("MQTT disconnected")

    def _unsafe_publish(self, device: str, control: str, value: Any, retain: bool = True) -> None:
        topic: str = f"/devices/{device}/controls/{control}"
        self._send_message(topic, value, retain)

    def _send_message(self, topic: str, message: Any, retain: bool = True):
        try:
            self.client.publish(topic, payload=message, qos=1, retain=retain)
            LOGGER.debug(f"MQTT published. Topic={topic}, message={message}")
        except Exception:
            LOGGER.error(f"Publish message error. Topic={topic}, message={message}", exc_info=True)

    def _send_device_meta(self, device_meta: WbDeviceMeta):
        for field_name, field_value in device_meta.get_meta().items():
            topic: str = f"/devices/{device_meta.deviceName}/meta/{field_name}"
            self._send_message(topic, field_value)

    def _send_control_meta(self, device_name: str, control_name: str, control_meta: WbDeviceControlMeta):
        for field_name, field_value in control_meta.get_meta().items():
            topic: str = f"/devices/{device_name}/controls/{control_name}/meta/{field_name}"
            self._send_message(topic, field_value)
