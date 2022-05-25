# TODO
# * Remindme
# TODO

import discord.ext.commands
from discord.ext import commands


class ReminderCog(commands.Cog, name="Reminder Commands"):
    @commands.command()
    async def remindme(self, ctx: discord.ext.commands.Context):
        ...


def setup(bot: commands.Bot):
    bot.add_cog(ReminderCog(bot))
