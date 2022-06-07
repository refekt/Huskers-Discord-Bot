# TODO
# * Deepfry
# * Hypeme
# * Img(create, delete, list, random)
# * Inspireme
# * Slowking
# TODO

import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class ImageCog(commands.Cog, name="Image Commands"):
    @commands.command()
    async def deepfry(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def inspireme(self, interaction: discord.Interaction):
        ...

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
