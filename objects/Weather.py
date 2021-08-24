class WeatherHour:
    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)


class WeatherMain:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherCoord:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherSys:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherWeather:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherWind:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherClouds:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherRain:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherSnow:

    def __init__(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        self._data_len = len(dictionary)

    def __len__(self):
        return self._data_len


class WeatherResponse:

    def __init__(self, dictionary):
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
                setattr(self, key, value)
