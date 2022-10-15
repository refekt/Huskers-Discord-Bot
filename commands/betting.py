import logging
import platform
from datetime import datetime, timedelta
from typing import Optional, Union

import discord.ext.commands
from discord import app_commands
from discord.app_commands import Group
from discord.ext import commands

from helpers.constants import (
    DEBUGGING_CODE,
    FIELDS_LIMIT,
    GUILD_PROD,
    TZ,
)
from helpers.embed import buildEmbed
from helpers.mysql import processMySQL, sqlGetBetsLeaderboard, sqlResolveGame
from objects.Bets_Stats_Schedule import (
    Bet,
    BigTenTeams,
    HuskerSched2022,
    WhichOverUnderChoice,
    WhichTeamChoice,
    retrieveGameBets,
    BettingHuskerSchedule,
)
from objects.Exceptions import BettingException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)


class BettingCog(commands.Cog, name="Betting Commands"):
    bet_group: Group = app_commands.Group(
        name="bet", description="Betting commands", guild_ids=[GUILD_PROD]
    )

    @bet_group.command(
        name="create", description="Place a bet against a Nebraska game."
    )
    @app_commands.describe(
        opponent="Name of the opponent_name for the Husker game.",
        game_winner="Whether you predict Nebraska or their opponent to win the game.",
        predict_points="Whether you predict the total points to go over or under.",
        predict_spread="Whether you predict Nebraska or their opponent to win against the spread.",
    )
    async def bet_create(
        self,
        interaction: discord.Interaction,
        opponent: HuskerSched2022,
        game_winner: WhichTeamChoice,
        predict_points: WhichOverUnderChoice,
        predict_spread: WhichTeamChoice,
    ) -> None:
        await interaction.response.defer()

        dt_str: str = f"{str(opponent).split('__')[1]}"
        dt: datetime = datetime.strptime(dt_str, "%Y-%m-%d").astimezone(tz=TZ)
        if "Windows" in platform.platform():
            dt += timedelta(hours=11)
        else:
            dt += timedelta(hours=12)
        dt_now: datetime = datetime.now(tz=TZ)

        logger.debug(f"Checking current time vs. game time: {dt_now} ~ {dt}")

        assert dt_now <= dt, BettingException(
            "You cannot place a bet after 11:00 AM of game days!"
        )

        assert game_winner != WhichTeamChoice.NA, BettingException(
            "Cannot choose 'Not Available' for the game winner!"
        )

        # game_started: bool = False
        # games_api: GamesApi = GamesApi(ApiClient(CFBD_CONFIG))
        # check_games: list[Game] = games_api.get_games(
        #     year=datetime.now().year,
        #     team=BigTenTeams.Nebraska.lower(),
        #     season_type="both",
        # )
        #
        # opponent_game: Optional[Game] = None
        # for game in check_games:
        #     if opponent not in (game.home_team, game.away_team):
        #         continue
        #     opponent_game = game
        #     break
        #
        # dt_start_date: datetime = datetime.strptime(
        #     opponent_game.start_date, DT_CFBD_GAMES
        # ).astimezone(tz=TZ)
        #
        # if dt_start_date.astimezone(tz=TZ) < datetime.now(tz=TZ):
        #     await interaction.response.send(
        #         f"You cannot place a bet on {opponent} after the game has started!",
        #         ephemeral=True,
        #     )
        # else:
        #     await interaction.response.defer()

        if [_ for _ in (game_winner, predict_points, predict_spread) if _ is None]:
            raise BettingException("You cannot submit a blank bet!")

        assert game_winner is not None, BettingException(
            "`predict_game` is the minimum bet and must be included."
        )

        bet: Bet = Bet(
            author=interaction.user,
            opponent_name=opponent,
            predict_game=game_winner,
            predict_points=predict_points,
            predict_spread=predict_spread,
        )
        try:
            bet.submitRecord()
        except BettingException:
            logger.exception("Error submitting the bet to the MySQL database.")
            return

        embed: discord.Embed = buildEmbed(
            title=f"Nebraska vs. {opponent} Bet",
            description=str(bet.bet_lines)
            if bet.bet_lines
            else "Betting lines not available.",
            fields=[
                dict(
                    name=f"{interaction.user.display_name} ({interaction.user.name}#{interaction.user.discriminator})'s Bet",
                    value=f"Wins: {bet.predict_game}\n"
                    f"Total Points: {bet.predict_points}\n"
                    f"Against the Spread: {bet.predict_spread}\n",
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
        self, interaction: discord.Interaction, opponent_name: BettingHuskerSchedule
    ):
        await interaction.response.defer()

        opponent_bets: Union[list[dict], dict, None] = retrieveGameBets(
            school_name=opponent_name, _all=True
        )

        if opponent_bets is None:
            embed: discord.Embed = buildEmbed(
                title=f"{BigTenTeams.Nebraska} vs. {opponent_name.value} Bets",
                description=f"No bets found for {interaction.user.mention}",
            )
        else:
            total_wins: dict[str, int] = {"Nebraska": 0, "Opponent": 0}
            total_overunder: dict[str, int] = {"Over": 0, "Under": 0}
            total_spread: dict[str, int] = {"Nebraska": 0, "Opponent": 0}
            fields: list[dict[str, str]] = []

            for bet in opponent_bets:
                total_wins[bet.get("predict_game")] += 1

                if "Not Available" not in bet.get("predict_points"):
                    total_overunder[bet.get("predict_points")] += 1

                if "Not Available" not in bet.get("predict_spread"):
                    total_spread[bet.get("predict_spread")] += 1

                fields.append(
                    dict(
                        name=f"{bet.get('author_str', 'N/A').upper()}",
                        value=(
                            f"Wins: {bet.get('predict_game', 'N/A')}\n"
                            f"Total Points: {bet.get('predict_points', 'N/A')}\n"
                            f"Against the Spread: {bet.get('predict_spread', 'N/A')}\n"
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

    @bet_group.command(
        name="leaderboard",
        description="Show the leaderboard for betting",
    )
    async def bet_leaderboard(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer()

        all_bets: Optional[list[dict, ...]] = processMySQL(
            query=sqlGetBetsLeaderboard, fetch="all"
        )
        if all_bets is not None and len(all_bets) > FIELDS_LIMIT:
            all_bets = all_bets[0 : FIELDS_LIMIT - 1]

        bet_title: str = "2022 Husker Betting Leaderboard"

        if all_bets:
            embed: discord.Embed = buildEmbed(
                title=bet_title,
                description="Point weights: 1x win, 2x points, 2x spread",
                fields=[
                    dict(
                        name=f"#{index + 1}",
                        value=f"{bet['author_str']} - {bet['average_points_per_game']} pts\n({bet['correct_wins']} Wins, {bet['correct_overunder']} Total Points, {bet['correct_spread']} Against the Spread)",
                    )
                    for (index, bet) in enumerate(all_bets)
                ],
            )
        else:
            embed = buildEmbed(
                title=bet_title,
                description="Point weights: 1x win, 2x points, 2x spread",
                fields=[
                    dict(
                        name="No Bets Found!",
                        value="Check back after a game has been resolved",
                    )
                ],
            )

        await interaction.followup.send(embed=embed)

    @bet_group.command(
        name="resolve", description="Resolve a game to update the leaderboard"
    )
    @app_commands.describe(
        opponent_name="Name of the opponent",
        game_winner="Who won the game",
        result_points="Were the total points over or under",
        result_spread="Who won the spread",
    )
    @app_commands.default_permissions(administrator=True)
    async def bet_resolve(
        self,
        interaction: discord.Interaction,
        opponent_name: HuskerSched2022,
        game_winner: WhichTeamChoice,
        result_points: WhichOverUnderChoice,
        result_spread: WhichTeamChoice,
    ):
        await interaction.response.defer(ephemeral=True)

        processMySQL(
            query=sqlResolveGame,
            values=(
                game_winner,
                result_points,
                result_spread,
                opponent_name,
            ),
        )

        await interaction.followup.send(
            f"Updated the {opponent_name} game with {game_winner} winning, {result_points} on the points, and {result_spread} on the spread."
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BettingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
