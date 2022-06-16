import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class ReminderCog(commands.Cog, name="Reminder Commands"):
    @commands.command()
    async def remindme(self, interaction: discord.Interaction):
        await interaction.response.send_message("Not implemented yet!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReminderCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
