# TODO
# * Crootbot
# * FAP(predict, leaderboard, stats, user)
# TODO
import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class RecruitingCog(commands.Cog, name="Recruiting Commands"):
    @commands.command()
    async def crootbot(self, interaction: discord.Interaction):
        ...

    @commands.command()
    async def fap(
        self, interaction: discord.Interaction
    ):  # predict, stats, leaderboard, user
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecruitingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
