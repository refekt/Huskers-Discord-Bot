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
        who_wins="Whether you predict Nebraska or their opponent to win the game.",
        over_under_points="Whether you predict the points to go over or under.",
        over_under_spread="Whether you predict the spread to go over or under.",
    )
    async def bet_game(
        self,
        interaction: discord.Interaction,
        opponent_name: HuskerSched2022,
        who_wins: Optional[WhichTeamChoice],
        over_under_points: Optional[WhichOverUnderChoice],
        over_under_spread: Optional[WhichOverUnderChoice],
    ) -> None:
        await interaction.response.defer()

        assert None not in (
            who_wins,
            over_under_points,
            over_under_spread,
        ), BettingException("You cannot submit a blank bet!")

        assert who_wins is not None, BettingException(
            "`who_wins` is the minimum bet and must be included."
        )

        bet = Bet(
            author=interaction.user,
            opponent_name=opponent_name,
            who_wins=who_wins,
            over_under_points=over_under_points,
            over_under_spread=over_under_spread,
        )
        try:
            bet.submitRecord()
        except BettingException:
            logger.error("Error submitting the bet to the MySQL database.")
            return

        embed = buildEmbed(
            title=f"Nebraska vs. {opponent_name} Bet",
            description=str(bet.bet_lines),
            fields=[
                dict(
                    name=f"{interaction.user.display_name} ({interaction.user.name}#{interaction.user.discriminator})'s Bet",
                    value=f"Wins: {bet.who_wins}\n"
                    f"Over/Under: {bet.over_under_points}\n"
                    f"Spread: {bet.over_under_spread}",
                )
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
                        value=f"Wins: {bet.get('who_wins', 'N/A')}\n"
                        f"Over/Under: {bet.get('over_under_points', 'N/A')}\n"
                        f"Spread: {bet.get('over_under_spread', 'N/A')}",
                    )
                    for bet in opponent_bets
                ],
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
