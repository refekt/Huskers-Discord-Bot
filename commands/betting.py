import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD
from helpers.embed import buildEmbed
from objects.Bets_Stats_Schedule import Bet, WhichTeamChoice, HuskerSched2022
from objects.Exceptions import BettingException
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class BettingCog(commands.Cog, name="Betting Commands"):
    @app_commands.command(
        name="bet", description="Place a bet against a Nebraska game."
    )
    @app_commands.describe(
        opponent="Name of the opponent for the Husker game.",
        which_team="Which team you predict to win.",
    )
    @app_commands.guilds(GUILD_PROD)
    async def bet(
        self,
        interaction: discord.Interaction,
        opponent: HuskerSched2022,
        which_team: WhichTeamChoice,
    ) -> None:
        await interaction.response.defer()

        bet = Bet(author=interaction.user, opponent=opponent, which_team=which_team)
        try:
            bet.submitRecord()
        except BettingException:
            logger.exception("Error submitting the bet to the MySQL database.")
            return

        embed = buildEmbed(
            title="Husker Schedule Betting",
            fields=[
                dict(name="Placed Bet", value=str(bet)),
                dict(name="Betting Lines", value=str(bet.bet_lines)),
            ],
            author=bet.author_str,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
