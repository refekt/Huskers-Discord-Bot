import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from objects.Bets_Stats_Schedule import Bet, BigTenTeams, WhichTeamChoice
from objects.Exceptions import BettingException
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class BettingCog(commands.Cog, name="Betting Commands"):
    @app_commands.command(name="bet", description="TBD")
    @app_commands.guilds(GUILD_PROD)
    async def bet(
        self,
        interaction: discord.Interaction,
        opponent: BigTenTeams,
        which_team: WhichTeamChoice,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        bet = Bet(author=interaction.user, opponent=opponent, which_team=which_team)
        try:
            bet.submitRecord()
        except BettingException:
            logger.exception("Error submitting the bet to the MySQL database.")
            return

        await interaction.followup.send(f"{bet} {str(bet.bet_lines)}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
