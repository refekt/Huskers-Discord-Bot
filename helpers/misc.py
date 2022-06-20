import inspect
import logging
import pathlib
import platform
import random
import string
from datetime import datetime

from objects.Exceptions import CommandException, StatsException

logger = logging.getLogger(__name__)

__all__ = [
    "checkYearValid",
    "createComponentKey",
    "discordURLFormatter",
    "getModuleMethod",
    "loadVarPath",
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


def getModuleMethod(stack) -> tuple:
    frm: inspect.FrameInfo = stack[1]
    mod = inspect.getmodule(frm[0]).__name__
    method = frm[3]
    return mod, method


logger.info(f"{str(__name__).title()} module loaded!")
