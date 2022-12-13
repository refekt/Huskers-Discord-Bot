import logging
from datetime import datetime, timezone

from helpers.constants import TZ
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__: list[str] = ["WeatherResponse", "WeatherHour"]


class WeatherHour:
    __slots__ = [
        "_data_len",
        "clouds",
        "dew_point",
        "dt",
        "feels_like",
        "humidity",
        "pop",
        "pressure",
        "rain",
        "snow",
        "temp",
        "uvi",
        "visibility",
        "weather",
        "wind_deg",
        "wind_gust",
        "wind_speed",
    ]

    def __init__(self, dictionary) -> None:
        self.wind_speed = None
        self.temp = None
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)


class WeatherMain:
    __slots__ = [
        "_data_len",
        "feels_like",
        "grnd_level",
        "humidity",
        "pressure",
        "sea_level",
        "temp",
        "temp_max",
        "temp_min",
    ]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherCoord:
    __slots__ = ["lon", "lat", "_data_len"]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherSys:
    __slots__ = ["type", "id", "country", "sunrise", "sunset", "_data_len"]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            if key == "sunrise":
                self.sunrise = datetime.fromtimestamp(value, timezone.utc).astimezone(
                    tz=TZ
                )
            elif key == "sunset":
                self.sunset = datetime.fromtimestamp(value, timezone.utc).astimezone(
                    tz=TZ
                )
            else:
                setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherWeather:
    __slots__ = ["id", "main", "description", "icon", "_data_len"]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherWind:
    __slots__ = ["speed", "deg", "gust", "_data_len"]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherClouds:
    __slots__ = ["all", "_data_len"]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherRain:
    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherSnow:
    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self) -> int:
        return self._data_len


class WeatherResponse:
    __slots__ = [
        "base",
        "clouds",
        "cod",
        "coord",
        "dt",
        "id",
        "main",
        "name",
        "rain",
        "snow",
        "sys",
        "timezone",
        "visibility",
        "weather",
        "wind",
    ]

    def __init__(self, dictionary) -> None:
        for key, value in dictionary.items():
            if key == "main":
                self.main = WeatherMain(value)
            elif key == "coord":
                self.coord = WeatherCoord(value)
            elif key == "sys":
                self.sys = WeatherSys(value)
            elif key == "weather":
                self.weather = []
                for item in value:
                    self.weather.append(WeatherWeather(item))
            elif key == "wind":
                self.wind = WeatherWind(value)
            elif key == "clouds":
                self.clouds = WeatherClouds(value)
            elif key == "rain":
                self.rain = WeatherRain(value)
            elif key == "snow":
                self.snow = WeatherSnow(value)
            else:
                if key == "dt":
                    self.dt = datetime.utcfromtimestamp(value).astimezone(
                        tz=timezone.utc
                    )
                else:
                    setattr(self, key, value)


logger.info(f"{str(__name__).title()} module loaded!")
