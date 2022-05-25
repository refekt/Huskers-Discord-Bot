# TODO
# * Countdown
# * Compare
# * Schedule
# * Teamstats
# * Seasonstats
# TODO


import discord.ext.commands
from discord.ext import commands


class StatsCog(commands.Cog, name="Stats Commands"):
    @commands.command()
    async def countdown(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def compare(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def schedule(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def stats(self, ctx: discord.ext.commands.Context):  # Team and season
        ...


def setup(bot: commands.Bot):
    bot.add_cog(StatsCog(bot))
