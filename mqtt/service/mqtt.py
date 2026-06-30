from typing import Any

import paho.mqtt.client as mqtt

from common.config import get_service_and_config_paths
from common.config import load_config_json
from common.logger import configure_logger
from mqtt.dto.dto import MQTTConfig

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("mqtt")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"

LOGGER = configure_logger("logs", LOG_PATH)


class MQTTPublisher:
    instance = None

    @staticmethod
    def get_instance():
        if MQTTPublisher.instance is None:
            MQTTPublisher.instance = MQTTPublisher()
        return MQTTPublisher.instance

    def __init__(self):
        try:
            config: MQTTConfig = MQTTConfig(load_config_json(SETTINGS_FILE))
            self.client = mqtt.Client(client_id=config.client_id)
            self.client.connect(config.host, config.port, keepalive=60)
            self.client.loop_start()
            LOGGER.info("MQTT connected")
        except Exception:
            LOGGER.error("MQTT connect error: ", exc_info=True)

    def publish(self, device: str, control: str, value: Any, retain: bool = True) -> None:
        topic = f"/devices/{device}/controls/{control}"
        self._send_message(topic, value, retain)

    def _send_message(self, topic: str, message: Any, retain: bool = True):
        try:
            self.client.publish(topic, payload=message, qos=1, retain=retain)
            LOGGER.debug(f"MQTT published. Topic={topic}, message={message}")
        except Exception:
            LOGGER.error(f"Publish message error. Topic={topic}, message={message}", exc_info=True)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        LOGGER.info("MQTT disconnected")
