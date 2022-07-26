import functools
import inspect
import logging
import pathlib
import platform
import random
import string
from datetime import datetime, timedelta
from typing import Callable, Union, Any

from objects.Exceptions import CommandException, StatsException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if "Windows" in platform.platform() else logging.INFO,
)

__all__: list[str] = [
    "alias_param",
    "checkYearValid",
    "convertSeconds",
    "createComponentKey",
    "discordURLFormatter",
    "getModuleMethod",
    "loadVarPath",
    "shift_utc_tz",
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


def convertSeconds(n) -> Union[int, Any]:
    logger.info(f"Converting {n:,} seconds to hours and minutes")
    secs = n % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60
    return hour, mins


def shift_utc_tz(dt: datetime, shift: int) -> datetime:
    return dt + timedelta(seconds=shift)


logger.info(f"{str(__name__).title()} module loaded!")
