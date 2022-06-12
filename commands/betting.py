import discord.ext.commands
from discord.ext import commands

from helpers.constants import GUILD_PROD


class BettingCog(commands.Cog, name="Betting Commands"):
    @commands.command()
    async def remindme(self, interaction: discord.Interaction):
        await interaction.response.send_message("Not implemented yet!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
