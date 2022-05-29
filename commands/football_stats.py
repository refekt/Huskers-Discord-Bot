# TODO
# * Countdown
# * Compare
# * Schedule
# * Teamstats
# * Seasonstats
# TODO


import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class StatsCog(commands.Cog, name="Stats Commands"):
    @commands.command()
    async def countdown(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def compare(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def schedule(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def stats(self, ctx: discord.interactions.Interaction):  # Team and season
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(StatsCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
