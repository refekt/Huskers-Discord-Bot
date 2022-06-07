# TODO
# * Deepfry
# * Hypeme
# * Img(create, delete, list, random)
# * Inspireme
# * Slowking
# TODO
import logging
import pathlib
import platform
from typing import Optional

import discord.ext.commands
import requests
from PIL import Image, ImageOps, ImageDraw
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Exceptions import ImageException

logger = logging.getLogger(__name__)


class ImageCog(commands.Cog, name="Image Commands"):
    @commands.command()
    async def deepfry(self, interaction: discord.Interaction):
        ...

    @app_commands.command(
        name="inspire-me",
        description="Get random inspiration",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(GUILD_PROD)
    async def inspireme(
        self, interaction: discord.Interaction, person: Optional[discord.Member] = None
    ):
        image = requests.get("https://inspirobot.me/api?generate=true")

        if person:
            await interaction.response.send_message(
                f"{interaction.user.mention} wants to inspire {person.mention}\n"
                f"{image.text}"
            )
        else:
            await interaction.response.send_message(image.text)

    @app_commands.command(
        name="slowking",
        description="Crown someone as a Slowking",
    )
    @app_commands.describe(person="Person you want to inspire")
    @app_commands.guilds(GUILD_PROD)
    async def slowking(self, interaction: discord.Interaction, person: discord.Member):
        await interaction.response.defer()

        try:
            avatar_thumbnail = Image.open(
                requests.get(person.avatar.url, stream=True).raw
            ).convert("RGBA")
        except IOError:
            logger.exception("Unable to create a Slow King avatar for user!")
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

        await interaction.followup.send(content=person.mention, file=file)

        file.close()

    @commands.command()
    async def img(
        self, interaction: discord.Interaction
    ):  # create, list, delete, random
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
