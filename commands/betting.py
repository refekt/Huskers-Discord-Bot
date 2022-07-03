from typing import Optional

import discord.ext.commands
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from helpers.constants import GUILD_PROD, GUILD_TEST
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
        name="bet", description="Betting commands", guild_ids=[GUILD_PROD, GUILD_TEST]
    )

    @bet_group.command(name="game", description="Place a bet against a Nebraska game.")
    @app_commands.describe(
        opponent_name="Name of the opponent_name for the Husker game.",
        who_wins="Whether you predict Nebraska or their opponent to win the game.",
        over_under_points="Whether you predict the points to go over or under.",
        over_under_spread="Whether you predict Nebraska or their opponent to win against the spread.",
    )
    async def bet_game(
        self,
        interaction: discord.Interaction,
        opponent_name: HuskerSched2022,
        who_wins: Optional[WhichTeamChoice],
        over_under_points: Optional[WhichOverUnderChoice],
        over_under_spread: Optional[WhichTeamChoice],
    ) -> None:
        await interaction.response.defer()

        if [_ for _ in (who_wins, over_under_points, over_under_spread) if _ is None]:
            raise BettingException("You cannot submit a blank bet!")

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
            description=str(bet.bet_lines)
            if bet.bet_lines
            else "Betting lines not available.",
            fields=[
                dict(
                    name=f"{interaction.user.display_name} ({interaction.user.name}#{interaction.user.discriminator})'s Bet",
                    value=f"Wins: {bet.who_wins}\n"
                    f"Against the Spread: {bet.over_under_spread}\n"
                    f"Total Points: {bet.over_under_points}",
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
            total_wins: dict[str, int] = {"Nebraska": 0, "Opponent": 0}
            total_spread: dict[str, int] = {"Nebraska": 0, "Opponent": 0}
            total_overunder: dict[str, int] = {"Over": 0, "Under": 0}
            fields: list[dict[str, str]] = []

            for bet in opponent_bets:
                total_wins[bet.get("which_team_wins")] += 1
                total_spread[bet.get("which_team_spread")] += 1
                total_overunder[bet.get("which_team_overunder")] += 1

                fields.append(
                    dict(
                        name=f"{bet.get('author_str', 'N/A')}'s Bet",
                        value=(
                            f"Wins: {bet.get('which_team_wins', 'N/A')}\n"
                            f"Total Points: {bet.get('which_team_spread', 'N/A')}\n"
                            f"Against the Spread: {bet.get('which_team_overunder', 'N/A')}\n"
                        ),
                    )
                )

            col_width: int = 6
            totals_str: str = (
                f"```\n"
                f"{'Which':<8}|{'Wins':<4}|{'Spread':<6}|{' ' * 6}|{'Points':<{col_width}}\n"
                f"{'Nebraska':<8}|{total_wins['Nebraska']:<4}|{total_spread['Nebraska']:<6}|{'Over':<6}|{total_overunder['Over']:<{col_width}}\n"
                f"{'Opponent':<8}|{total_wins['Opponent']:<4}|{total_spread['Opponent']:<6}|{'Under':<6}|{total_overunder['Under']:<{col_width}}\n"
                f"```"
            )

            embed = buildEmbed(
                title=f"{BigTenTeams.Nebraska} vs. {opponent_name.value} Bets",
                description=totals_str,
                fields=fields,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
