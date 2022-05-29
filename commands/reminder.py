# TODO
# * Remindme
# TODO

import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class ReminderCog(commands.Cog, name="Reminder Commands"):
    @commands.command()
    async def remindme(self, ctx: discord.interactions.Interaction):
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReminderCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
