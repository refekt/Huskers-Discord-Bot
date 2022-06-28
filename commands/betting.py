from typing import Optional

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
    WhichOverUnderChoice,
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
        opponent_name="Name of the opponent_name for the Husker game.",
        which_team_wins="Which team you predict to win.",
        which_team_overunder="Prediction for over/under.",
        which_team_spread="Which team you predict to cover the spread.",
    )
    async def bet_game(
        self,
        interaction: discord.Interaction,
        opponent_name: HuskerSched2022,
        which_team_wins: Optional[WhichTeamChoice],
        which_team_overunder: Optional[WhichOverUnderChoice],
        which_team_spread: Optional[WhichTeamChoice],
    ) -> None:
        await interaction.response.defer()

        bet = Bet(
            author=interaction.user,
            opponent_name=opponent_name,
            which_team_wins=which_team_wins,
            which_team_overunder=which_team_overunder,
            which_team_spread=which_team_spread,
        )
        try:
            bet.submitRecord()
        except BettingException:
            logger.error("Error submitting the bet to the MySQL database.")
            return

        embed = buildEmbed(
            title="Husker Schedule Betting",
            fields=[
                dict(
                    name="Placed Bet",
                    value=f"Wins: {bet.which_team_wins}\n"
                    f"Over/Under: {bet.which_team_overunder}\n"
                    f"Spread: {bet.which_team_spread}",
                ),
                dict(name="Betting Lines", value=str(bet.bet_lines)),
            ],
            author=bet.author_str,
            icon_url=interaction.user.display_avatar.url,
        )

        await interaction.followup.send(embed=embed)

    @bet_group.command(name="show", description="Show all bets for a specific game")
    @app_commands.describe(
        opponent_name="Name of the opponent_name for the Husker game."
    )
    async def bet_show(
        self, interaction: discord.Interaction, opponent_name: HuskerSched2022
    ):
        await interaction.response.defer()

        opponent_bets = retrieveGameBets(school_name=opponent_name, _all=True)

        if opponent_bets is None:
            embed = buildEmbed(
                title=f"{BigTenTeams.Nebraska} vs. {opponent_name.value} Bets",
                description=f"No bets found for {interaction.user.mention}",
            )
        else:
            embed = buildEmbed(
                title=f"{BigTenTeams.Nebraska} vs. {opponent_name.value} Bets",
                description="",
                fields=[
                    dict(
                        name=f"{bet.get('author_str', 'N/A')}'s Bet",
                        value=f"Wins: {bet.get('which_team_wins', 'N/A')}\n"
                        f"Over/Under: {bet.get('which_team_overunder', 'N/A')}\n"
                        f"Spread: {bet.get('which_team_spread', 'N/A')}",
                    )
                    for bet in opponent_bets
                ],
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
