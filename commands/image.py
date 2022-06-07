# TODO
# * Deepfry
# * Hypeme
# * Img(create, delete, list, random)
# * Inspireme
# * Slowking
# TODO
from typing import Optional

import discord.ext.commands
import requests
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


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

    @commands.command()
    async def slowking(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def img(
        self, interaction: discord.Interaction
    ):  # create, list, delete, random
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
