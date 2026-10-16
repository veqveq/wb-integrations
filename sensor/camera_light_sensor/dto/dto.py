from datetime import datetime

from common.utils import JsonDict


class CameraLightSensorSettings:
    def __init__(self, json: JsonDict):
        self.pool_interval = json.get("poolIntervalSec", 60)
        self.log_interval = json.get("logIntervalMin", 20) * 60


class LightSensorData:
    def __init__(
            self,
            middle: float,
            median: float,
            percentile5: float,
            percentile95: float,
            dark_pixels_percent: float,
            bright_pixels_percent: float,
            standard_deviation: float,
            light_level: float
    ):
        self.timestamp: datetime = datetime.now()
        self.middle: float = round(middle, 2)
        self.median: float = median
        self.percentile5: float = percentile5
        self.percentile95: float = percentile95
        self.dark_pixels_percent: float = round(dark_pixels_percent, 2)
        self.bright_pixels_percent: float = round(bright_pixels_percent, 2)
        self.standard_deviation: float = round(standard_deviation, 2)
        self.light_level: float = round(light_level, 2)

    def __str__(self):
        return (f'{self.timestamp},{self.middle},{self.median},{self.percentile5},{self.percentile95},'
                f',{self.dark_pixels_percent},{self.bright_pixels_percent},{self.standard_deviation}. '
                f'Level: {self.light_level}')


class LightSensorComponentRange:
    def __init__(self, min_val: float, max_val: float):
        self.min: float = min_val
        self.max: float = max_val
