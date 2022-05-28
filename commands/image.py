# TODO
# * Deepfry
# * Hypeme
# * Img(create, delete, list, random)
# * Inspireme
# * Slowking
# TODO

import discord.ext.commands
from discord.ext import commands


class ImageCog(commands.Cog, name="Image Commands"):
    @commands.command()
    async def deepfry(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def hypeme(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def inspireme(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def slowking(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def img(
        self, ctx: discord.ext.commands.Context
    ):  # create, list, delete, random
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageCog(bot))
