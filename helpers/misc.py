import logging
import pathlib
import platform
import random
import string

from objects.Exceptions import CommandException, UserInputException

logger = logging.getLogger(__name__)

__all__ = [
    "createComponentKey",
    "formatPrettyTimeDelta",
    "loadVarPath",
]


def formatPrettyTimeDelta(seconds) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return f"{days:,}D {hours}H, {minutes}M, and {seconds}S"
    elif hours > 0:
        return f"{hours}H, {minutes}M, and {seconds}S"
    elif minutes > 0:
        return f"{minutes}M and {seconds}S"
    else:
        return f"{seconds}S"


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


logger.info(f"{str(__name__).title()} module loaded!")
