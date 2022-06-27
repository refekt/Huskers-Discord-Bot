import discord.ext.commands
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from helpers.constants import GUILD_PROD
from helpers.embed import buildEmbed
from objects.Bets_Stats_Schedule import (
    Bet,
    WhichTeamChoice,
    HuskerSched2022,
    retrieveGameBets,
    BigTenTeams,
)
from objects.Exceptions import BettingException
from objects.Logger import discordLogger

logger = discordLogger(__name__)


class BettingCog(commands.Cog, name="Betting Commands"):
    bet_group: Group = app_commands.Group(
        name="bet", description="Betting commands", guild_ids=[GUILD_PROD]
    )

    @bet_group.command(name="game", description="Place a bet against a Nebraska game.")
    @app_commands.describe(
        opponent="Name of the opponent_name for the Husker game.",
        which_team="Which team you predict to win.",
    )
    async def bet_game(
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

    @bet_group.command(name="show", description="Show all bets for a specific game")
    @app_commands.describe(opponent="Name of the opponent_name for the Husker game.")
    async def bet_show(
        self, interaction: discord.Interaction, opponent: HuskerSched2022
    ):
        await interaction.response.defer()

        opponent_bets = retrieveGameBets(school_name=opponent, _all=True)

        embed = buildEmbed(
            title=f"{BigTenTeams.Nebraska} vs. {opponent.value} Bets",
            description="",
            fields=[
                dict(
                    name=f"{bet.get('author_str')}'s Bet",
                    value=f"{bet.get('which_team')}",
                )
                for bet in opponent_bets
            ],
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
