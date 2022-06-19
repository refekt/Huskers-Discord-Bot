from typing import Optional

import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class ReminderCog(commands.Cog, name="Reminder Commands"):
    @app_commands.command(name="remind-me", description="TBD")
    @app_commands.guilds(GUILD_PROD)
    async def remind_me(
        self,
        interaction: discord.Interaction,
        destination: discord.TextChannel,
        message: str,
        remind_who: Optional[discord.Member] = None,
    ) -> None:
        await interaction.response.send_message("Not implemented yet!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReminderCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
