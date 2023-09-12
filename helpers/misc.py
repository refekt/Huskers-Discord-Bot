from __future__ import annotations

import functools
import inspect
import json
import logging
import pathlib
import platform
import random
import string
from datetime import datetime, timedelta
from typing import Callable, Any, List

import discord
import requests

from helpers.constants import (
    DT_OPENWEATHER_UTC,
    HEADERS,
    TZ,
    US_STATES,
    WEATHER_API_KEY,
)
from helpers.embed import buildEmbed
from objects.Exceptions import CommandException, StatsException, WeatherException
from objects.Logger import discordLogger, is_debugging
from objects.Weather import WeatherResponse, WeatherHour

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__: list[str] = [
    "alias_param",
    "checkYearValid",
    "convertSeconds",
    "createComponentKey",
    "discordURLFormatter",
    "general_locked",
    "getModuleMethod",
    "loadVarPath",
    "shift_utc_tz",
    "weather_embed",
]


def loadVarPath() -> [str, CommandException]:
    myPlatform = platform.platform()
    if "Windows" in myPlatform:
        logger.info(f"Windows environment set")
        return pathlib.PurePath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/variables.json"
        )
    elif "Linux" in myPlatform:
        logger.info(f"Linux environment set")
        return pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/variables.json"
        )
    else:
        return CommandException(f"Unable to support {platform.platform()}!")


def createComponentKey() -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(10)
    )


def discordURLFormatter(display_text: str, url: str) -> str:
    return f"[{display_text}]({url})"


def checkYearValid(year: int) -> bool:
    if len(str(year)) == 2:
        year += 2000
    elif 1 < len(str(year)) < 4:
        raise StatsException("The search year must be two or four digits long.")
    if year > datetime.now().year + 5:
        raise StatsException(
            "The search year must be within five years of the current class."
        )
    if year < 1869:
        raise StatsException(
            "The search year must be after the first season of college football--1869."
        )
    return True


def getModuleMethod(stack) -> tuple[str, str]:
    frm: inspect.FrameInfo = stack[1]
    mod = inspect.getmodule(frm[0]).__name__
    method = frm[3]
    return mod, method


# https://stackoverflow.com/questions/41784308/keyword-arguments-aliases-in-python
def alias_param(param_name: str, param_alias: str) -> None:
    """
    Decorator for aliasing a param in a function

    Args:
        param_name: name of param in function to alias
        param_alias: alias that can be used for this param
    Returns:
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Callable:
            alias_param_value = kwargs.get(param_alias)
            if alias_param_value:
                kwargs[param_name] = alias_param_value
                del kwargs[param_alias]
            result = func(*args, **kwargs)
            return result

        return wrapper


def convertSeconds(n) -> int | Any:
    logger.info(f"Converting {n:,} seconds to hours and minutes")
    secs = n % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60
    return hour, mins


def shift_utc_tz(dt: datetime, shift: int) -> datetime:
    return dt + timedelta(seconds=shift)


def general_locked(
    gen_c: discord.TextChannel, gen_check: discord.Role | discord.Member
) -> bool:
    return not gen_c.permissions_for(gen_check).send_messages


def weather_embed(
    city: str,
    state: str,
    country: str = "US",
) -> discord.Embed:
    try:
        formatted_state: dict[str] = next(
            (
                search_state
                for search_state in US_STATES
                if (
                    search_state["State"].lower() == state.lower()
                    or search_state["Abbrev"][:-1].lower() == state.lower()
                    or search_state["Code"].lower() == state.lower()
                )
            ),
            None,
        )
    except StopIteration:
        raise WeatherException("Unable to find state. Please try again!")

    weather_url: str = f"https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API_KEY}&units=imperial&lang=en&q={city},{formatted_state['Code']},{country}"
    response: requests.Response = requests.get(weather_url, headers=HEADERS)
    j: dict = json.loads(response.content)

    weather: WeatherResponse = WeatherResponse(j)
    if weather.cod == "404":
        raise WeatherException(f"Unable to find {city.title()}, {state}. Try again!")

    temp_str: str = (
        f"Temperature: {weather.main.temp}℉\n"
        f"Feels Like: {weather.main.feels_like}℉\n"
        f"Humidity: {weather.main.humidity}%\n"
        f"Max: {weather.main.temp_max}℉\n"
        f"Min: {weather.main.temp_min}℉"
    )

    if len(weather.wind) == 2:
        wind_str: str = (
            f"Speed: {weather.wind.speed} MPH\n" f"Direction: {weather.wind.deg} °"
        )
    elif len(weather.wind) == 3:
        wind_str = (
            f"Speed: {weather.wind.speed} MPH\n"
            f"Gusts: {weather.wind.gust} MPH\n"
            f"Direction: {weather.wind.deg}°"
        )
    else:
        wind_str = f"Speed: {weather.wind.speed} MPH"

    hourly_url: str = f"https://api.openweathermap.org/data/2.5/onecall?lat={weather.coord.lat}&lon={weather.coord.lon}&appid={WEATHER_API_KEY}&units=imperial"
    response: requests.Response = requests.get(hourly_url, headers=HEADERS)
    j: dict = json.loads(response.content)
    hours: List[WeatherHour] = []
    for index, item in enumerate(j["hourly"]):
        hours.append(WeatherHour(item))
        if index == 3:
            break

    hour_temp_str: str = ""
    hour_wind_str: str = ""
    for index, hour in enumerate(hours):
        if index < len(hours) - 1:
            hour_temp_str += f"{hour.temp}℉ » "
            hour_wind_str += f"{hour.wind_speed} MPH » "
        else:
            hour_temp_str += f"{hour.temp}℉"
            hour_wind_str += f"{hour.wind_speed} MPH"

    sunrise: datetime = weather.sys.sunrise
    sunset: datetime = weather.sys.sunset

    sun_str: str = (
        f"Sunrise: {sunrise.astimezone(tz=TZ).strftime(DT_OPENWEATHER_UTC)}\n"
        f"Sunset: {sunset.astimezone(tz=TZ).strftime(DT_OPENWEATHER_UTC)}"
    )

    embed: discord.Embed = buildEmbed(
        title=f"Weather conditions for {city.title()}, {state.upper()}",
        description=f"It is currently {weather.weather[0].main} with {weather.weather[0].description}.",
        fields=[
            dict(
                name="Temperature",
                value=temp_str,
            ),
            dict(
                name="Clouds",
                value=f"Coverage: {weather.clouds.all}%",
            ),
            dict(
                name="Wind",
                value=wind_str,
            ),
            dict(
                name="Temp Next 4 Hours",
                value=hour_temp_str,
            ),
            dict(
                name="Wind Next 4 Hours",
                value=hour_wind_str,
            ),
            dict(
                name="Sun",
                value=sun_str,
            ),
        ],
        thumbnail=f"https://openweathermap.org/img/wn/{weather.weather[0].icon}@4x.png",
    )

    return embed


logger.info(f"{str(__name__).title()} module loaded!")
