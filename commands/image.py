# TODO
# * Deepfry
# * Hypeme
# * Img(create, delete, list, random)
# * Inspireme
# * Slowking
# TODO

import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class ImageCog(commands.Cog, name="Image Commands"):
    @commands.command()
    async def deepfry(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def hypeme(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def inspireme(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def slowking(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def img(
        self, ctx: discord.interactions.Interaction
    ):  # create, list, delete, random
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
