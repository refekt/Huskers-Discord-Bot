# TODO
# * Crootbot
# * FAP(predict, leaderboard, stats, user)
# TODO
import discord.ext.commands
from discord.ext import commands


class RecruitingCog(commands.Cog, name="Recruiting Commands"):
    @commands.command()
    async def crootbot(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def fap(
        self, ctx: discord.ext.commands.Context
    ):  # predict, stats, leaderboard, user
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecruitingCog(bot))
