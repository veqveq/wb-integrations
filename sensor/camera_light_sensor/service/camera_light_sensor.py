import asyncio

from cv2 import imdecode, IMREAD_COLOR, cvtColor, COLOR_BGR2HSV
from numpy import frombuffer, ndarray, uint8, median, percentile, count_nonzero, std

from common.config import get_service_and_config_paths, load_config_json, get_config_path
from common.logger import configure_logger
from hikvision.camera.dto.dto import HikvisionCameraConfig
from hikvision.camera.service.camera import HikvisionCamera
from mqtt.service.mqtt import MQTTPublisher
from sensor.camera_light_sensor.dto.dto import LightSensorData, CameraLightSensorSettings

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("sensor/camera_light_sensor")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
CAMERAS_FILE = get_config_path("security/camera_alarm") / "cameras.json"

LOGGER = configure_logger("logs", LOG_PATH)


class CameraLightSensor:
    components_weight: dict[str, float] = {
        "median": 0.40,
        "percentile5": 0.20,
        "middle": 0.15,
        "dark_pixels_percent": 0.10,
        "standard_deviation": 0.10,
        "bright_pixels_percent": 0.05
    }

    def __init__(self, camera_config: HikvisionCameraConfig):
        settings = CameraLightSensorSettings(load_config_json(SETTINGS_FILE))
        self.pool_interval = settings.pool_interval
        self.camera = HikvisionCamera(camera_config)
        self.mqtt = MQTTPublisher()
        self.mqtt.safe_publish(self.camera.meta, "lightSensorConnected", 1)
        self.light_level_avg = None

    async def close(self):
        await self.camera.close()
        self.mqtt.safe_publish(self.camera.meta, "lightLevel", None)
        self.mqtt.safe_publish(self.camera.meta, "lightSensorConnected", 0)
        self.mqtt.disconnect()

    async def calculate_lighting_level(self):
        try:
            snapshot_bytes = await self.camera.get_snapshot()
            snapshot_array: ndarray = frombuffer(snapshot_bytes, dtype=uint8)
            snapshot: ndarray = imdecode(snapshot_array, IMREAD_COLOR)
            hsv: ndarray = cvtColor(snapshot, COLOR_BGR2HSV)
            light_sensor_data: LightSensorData = self._calculate_light_sensor_data(hsv)
            light_level = round(sum([fld_value * self.components_weight[fld_name]
                                     for fld_name, fld_value in vars(light_sensor_data).items()
                                     if fld_name in self.components_weight
                                     ]), 2)
            if self.light_level_avg is None:
                self.light_level_avg = light_level
            self.light_level_avg = round(0.8 * self.light_level_avg + 0.2 * light_level, 0)
            self.mqtt.safe_publish(self.camera.meta, "lightLevel", self.light_level_avg)
            LOGGER.debug(f'{self.camera.name}: {self.light_level_avg}')
        except Exception:
            LOGGER.error(f'Calculate lighting level error. Camera: {self.camera.name}', exc_info=True)
            return None
        finally:
            await asyncio.sleep(self.pool_interval)

    @staticmethod
    def _calculate_light_sensor_data(hsv: ndarray) -> LightSensorData:
        value_channel = hsv[:, :, 2]
        p5 = percentile(value_channel, 5)
        p95 = percentile(value_channel, 95)
        dark_pixels = count_nonzero(value_channel < p5)
        bright_pixels = count_nonzero(value_channel > p95)
        total_pixels = count_nonzero(value_channel)

        return LightSensorData(
            middle=value_channel.mean(),
            median=median(value_channel[(value_channel > p5) & (value_channel < p95)]),
            percentile5=p5,
            dark_pixels_percent=(1 - dark_pixels / total_pixels) * 100,
            bright_pixels_percent=bright_pixels / total_pixels * 100,
            standard_deviation=100 - std(value_channel)
        )


async def main():
    camera_configs = [HikvisionCameraConfig(config) for config in load_config_json(CAMERAS_FILE)]
    services = [CameraLightSensor(config) for config in camera_configs]
    try:
        while True:
            try:
                tasks = [service.calculate_lighting_level() for service in services]
                await asyncio.gather(*tasks)
            except Exception:
                LOGGER.error(f'Unnecessary error in calculate light_level iteration', exc_info=True)
                await asyncio.sleep(5)
    finally:
        for service in services:
            await service.close()


if __name__ == '__main__':
    asyncio.run(main())
