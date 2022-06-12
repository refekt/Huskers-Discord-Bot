import logging
import pathlib
import platform

import discord
import requests
from PIL import Image, ImageOps

from objects.Exceptions import ImageException

logger = logging.getLogger(__name__)

logger.info(f"{str(__name__).title()} module loaded!")


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
