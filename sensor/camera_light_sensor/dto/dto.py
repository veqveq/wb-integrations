from datetime import datetime

from common.utils import JsonDict


class CameraLightSensorSettings:
    def __init__(self, json: JsonDict):
        self.pool_interval = json.get("poolInterval", 60)


class LightSensorData:
    def __init__(
            self,
            middle: float,
            median: float,
            percentile5: int,
            dark_pixels_percent: float,
            bright_pixels_percent: float,
            standard_deviation: float
    ):
        self.timestamp: datetime = datetime.now()
        self.middle: float = round(middle, 2)
        self.median: float = median
        self.percentile5: int = percentile5
        self.dark_pixels_percent: float = round(dark_pixels_percent, 2)
        self.bright_pixels_percent: float = round(bright_pixels_percent, 2)
        self.standard_deviation: float = round(standard_deviation, 2)

    def __str__(self):
        return (f'{self.timestamp},{self.middle},{self.median},{self.percentile5},'
                f',{self.dark_pixels_percent},{self.bright_pixels_percent},{self.standard_deviation}')
