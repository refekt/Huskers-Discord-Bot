import logging
import pathlib
import platform
import random
import string

import discord
import requests
from PIL import ImageOps
from PIL import Image

from objects.Exceptions import CommandException, ImageException

logger = logging.getLogger(__name__)

__all__ = [
    "createComponentKey",
    "discordURLFormatter",
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


def discordURLFormatter(display_text: str, url: str) -> str:
    return f"[{display_text}]({url})"


def makeSlowking(person: discord.Member) -> discord.File:
    try:
        avatar_thumbnail = Image.open(
            requests.get(person.avatar.url, stream=True).raw
        ).convert("RGBA")
    except IOError:
        logger.exception("Unable to create a Slow King avatar for user!", exc_info=True)
        raise ImageException("Unable to create a Slow King avatar for user!")

    base_mask = Image.open("resources/images/mask.png").convert("L")
    avatar_thumbnail = ImageOps.fit(
        avatar_thumbnail, base_mask.size, centering=(0.5, 0.5)
    )
    avatar_thumbnail.putalpha(base_mask)

    paste_pos = (265, 250)
    slowking_filename = "make_slowking.png"

    base_img = Image.open("resources/images/slowking.png").convert("RGBA")
    base_img.paste(avatar_thumbnail, paste_pos, avatar_thumbnail)

    base_img.save(f"resources/images/{slowking_filename}", "PNG")

    if "Windows" in platform.platform():
        slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}\\resources\\images\\{slowking_filename}"
    else:
        slowking_path = f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/images/{slowking_filename}"

    with open(slowking_path, "rb") as f:
        file = discord.File(f)

    file.close()

    return file


logger.info(f"{str(__name__).title()} module loaded!")
