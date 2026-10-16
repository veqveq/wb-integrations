import asyncio
from datetime import datetime

from cv2 import imdecode, IMREAD_COLOR, cvtColor, COLOR_BGR2HSV, GaussianBlur
from numpy import frombuffer, ndarray, uint8, median, percentile, std, float32, mean, clip

from common.config import get_service_and_config_paths, load_config_json, get_config_path
from common.logger import configure_logger
from common.service import DebianService
from common.utils import CsvWriter
from hikvision.camera.dto.dto import HikvisionCameraConfig
from hikvision.camera.service.camera import HikvisionCamera
from mqtt.service.mqtt import MQTTPublisher
from sensor.camera_light_sensor.dto.dto import LightSensorData, CameraLightSensorSettings

SERVICE_PATH, CONFIG_PATH = get_service_and_config_paths("sensor/camera_light_sensor")

LOG_PATH = SERVICE_PATH / "logs"
SETTINGS_FILE = CONFIG_PATH / "settings.json"
CAMERAS_FILE = get_config_path("security/camera_alarm") / "cameras.json"

LOGGER = configure_logger("logs", LOG_PATH)


class CameraLightSensor(DebianService):
    def __init__(self, camera_config: HikvisionCameraConfig):
        super().__init__()
        self.cols = 5
        self.rows = 5
        settings = CameraLightSensorSettings(load_config_json(SETTINGS_FILE))
        self.pool_interval: int = settings.pool_interval
        self.log_interval: int = settings.log_interval
        self.camera: HikvisionCamera = HikvisionCamera(camera_config)
        self.mqtt: MQTTPublisher = MQTTPublisher()
        self.mqtt.safe_publish(self.camera.meta, "lightSensorConnected", 1)
        self.csv_writer: CsvWriter = CsvWriter(
            self.camera.meta.deviceName, LOG_PATH / f"research/", self._build_csv_header()
        )
        self.last_research_logged: datetime | None = None

    def _build_csv_header(self) -> list[str]:
        column_names: list = ["time"]
        for row in range(self.rows):
            for col in range(self.cols):
                column_names.append(f'{row + 1}-{col + 1}')
        return column_names

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
            value_channel = hsv[:, :, 2].astype(float32)
            light_sensor_data: LightSensorData = self._calculate_light_sensor_data(value_channel)
            self.mqtt.safe_publish(self.camera.meta, "lightLevel", light_sensor_data.light_level)
            # Ресерч
            # self._calculate_light_level_by_grid(value_channel)
        except Exception:
            LOGGER.error(f'Calculate lighting level error. Camera: {self.camera.name}', exc_info=True)
            return None
        finally:
            await asyncio.sleep(self.pool_interval)

    def _log_calculation_result(self, data: list):
        if self.last_research_logged is None:
            self.csv_writer.write_row(data)
            self.last_research_logged = datetime.now()
            return
        diff_sec = (datetime.now() - self.last_research_logged).total_seconds()
        if diff_sec > self.log_interval:
            self.csv_writer.write_row(data)
            self.last_research_logged = datetime.now()

    @staticmethod
    def _calculate_light_sensor_data(value_channel: ndarray) -> LightSensorData:
        value_channel = value_channel[value_channel < 220]

        p5 = float(percentile(value_channel, 5))
        p95 = float(percentile(value_channel, 95))
        m = float(median(value_channel))
        dark_percent = float(mean(value_channel < 30) * 100)
        bright_percent = float(mean(value_channel > 240) * 100)
        standard_deviation = float(std(value_channel))

        local_mean = GaussianBlur(value_channel, (0, 0), sigmaX=35, sigmaY=35)
        lavg = float(mean(local_mean))

        contrast = (p95 - p5) / 255.0
        contrast = clip(contrast, 0.0, 1.0)

        alpha = 0.25 + 0.35 * contrast
        alpha = clip(alpha, 0.25, 0.60)

        brightness = (1.0 - alpha) * m + alpha * lavg
        shadow_factor = 1.0 - dark_percent / 100.0
        shadow_factor = clip(shadow_factor, 0.70, 1.00)
        brightness *= shadow_factor

        light = (brightness - 30.0) / (120.0 - 30.0)
        light = clip(light, 0.0, 1.0)
        light = round(light * 100.0, 0)
        return LightSensorData(
            middle=lavg,
            median=m,
            percentile5=p5,
            percentile95=p95,
            dark_pixels_percent=dark_percent,
            bright_pixels_percent=bright_percent,
            standard_deviation=standard_deviation,
            light_level=light
        )

    def _calculate_light_level_by_grid(self, hsv: ndarray):
        grid: list[list] = self._split_to_grid(hsv)
        levels: list = [datetime.now().strftime("%d-%m-%Y %H:%M")]
        for row in range(self.rows):
            for col in range(self.cols):
                hsv: ndarray = grid[row][col]
                light_sensor_data: LightSensorData = self._calculate_light_sensor_data(hsv)
                levels.append(str(light_sensor_data.light_level))
        self._log_calculation_result(levels)

    def _split_to_grid(self, value_channel: ndarray):
        height, width = value_channel.shape
        cell_height = height // self.rows
        cell_widht = width // self.cols
        rows: list = []
        for row in range(self.rows):
            cols: list = []
            for col in range(self.cols):
                y1 = row * cell_height
                y2 = (row + 1) * cell_height if row != self.rows - 1 else height
                x1 = col * cell_widht
                x2 = (col + 1) * cell_widht if col != self.cols - 1 else width
                cols.append(value_channel[y1:y2, x1:x2].ravel())
            rows.append(cols)
        return rows


async def main():
    camera_configs = [HikvisionCameraConfig(config) for config in load_config_json(CAMERAS_FILE)]
    services = [CameraLightSensor(config) for config in camera_configs]
    try:
        while CameraLightSensor.is_running():
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
