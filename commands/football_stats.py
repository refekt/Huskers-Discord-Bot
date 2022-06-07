import calendar
import logging
from datetime import datetime
from typing import Union, Any

import discord
from cfbd import ApiClient, BettingApi, Configuration, GamesApi
from cfbd.rest import ApiException
from discord import app_commands
from discord.ext import commands

from helpers.constants import (
    CFBD_KEY,
    GUILD_PROD,
    TZ,
    DT_TBA_HR,
    DT_TBA_MIN,
    DT_OBJ_FORMAT_TBA,
    DT_OBJ_FORMAT,
)
from helpers.embed import buildEmbed
from objects.Exceptions import StatsException
from objects.Schedule import HuskerSchedule

logger = logging.getLogger(__name__)


cfbd_config = Configuration()
cfbd_config.api_key["Authorization"] = CFBD_KEY
cfbd_config.api_key_prefix["Authorization"] = "Bearer"


def convert_seconds(n) -> Union[int, Any]:
    logger.info(f"Converting {n:,} seconds to hours and minutes")
    secs = n % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60
    return hour, mins


def get_current_week(year: int, team: str) -> int:
    logger.info(f"Getting the current week for the {year} {team} game")
    api = GamesApi(ApiClient(cfbd_config))

    try:
        games = api.get_games(year=year, team=team)
    except ApiException:
        return -1

    for index, game in enumerate(games):
        if team == "Nebraska":
            if game.away_points is None and game.home_points is None:
                return game.week
        else:
            if any(
                [game.away_team == "Nebraska", game.home_team == "Nebraska"]
            ) and any([game.away_team == team, game.home_team == team]):
                return game.week


def get_consensus_line(
    team_name: str, year: int = datetime.now().year, week: int = None
) -> Union[None, str]:
    logger.info(f"Getting the conensus line for {year} Week {week} {team_name} game")

    cfb_api = BettingApi(ApiClient(cfbd_config))

    if week is None:
        week = get_current_week(year=year, team=team_name)

    try:
        api_response = cfb_api.get_lines(team=team_name, year=year, week=week)
    except (ApiException, TypeError):
        return None

    logger.info(f"API Response: {api_response}")

    try:
        # Hard code Week 0
        lines = None
        if len(api_response) > 1:
            for resp in api_response:
                if resp.away_team == "Nebraska":
                    lines = resp.lines[0]
                    break
        else:
            lines = api_response[0].lines[0]

        if lines is None:
            return None

        logger.info(f"Lines: {lines}")

        formattedSpread = (
            lines.get("formattedSpread") if lines.get("formattedSpread", None) else ""
        )
        spreadOpen = lines.get("spreadOpen") if lines.get("spreadOpen", None) else "N/A"
        overUnder = lines.get("overUnder") if lines.get("overUnder", None) else ""
        overUnderOpen = (
            lines.get("overUnderOpen") if lines.get("overUnderOpen", None) else "N/A"
        )
        homeMoneyline = (
            str(lines.get("homeMoneyline")) if lines.get("homeMoneyline", None) else ""
        )
        awayMoneyline = (
            str(lines.get("awayMoneyline")) if lines.get("awayMoneyline", None) else ""
        )

        new_line = "\n"
        consensus_line = (
            f"{'Spread: ' + formattedSpread + ' (Opened: ' + spreadOpen + ')' + new_line}"
            f"{'Over/Under:  ' + overUnder + ' (Opened: ' + overUnderOpen + ')' + new_line}"
            f"{'Home Moneyline: ' + homeMoneyline + new_line}"
            f"{'Away Moneyline: ' + awayMoneyline + new_line }"
        )

    except IndexError:
        consensus_line = None

    return consensus_line


class FootballStatsCog(commands.Cog, name="Football Stats Commands"):
    @app_commands.command(name="countdown")
    @app_commands.describe(
        opponent="Name of opponent to lookup", year="Year of the game to look up"
    )
    @app_commands.guilds(GUILD_PROD)
    async def countdown(
        self,
        interaction: discord.Interaction,
        opponent: str = None,
        year: int = datetime.now().year,
    ):
        logger.info(f"Starting countdown")
        await interaction.response.defer()

        now_cst = datetime.now().astimezone(tz=TZ)
        logger.info(f"Now CST is... {now_cst}")

        games, stats = HuskerSchedule(year=year)

        if not games:
            raise StatsException("No games found!")

        last_game = len(games) - 1
        now_cst_orig = None

        if games[last_game].game_date_time < now_cst:
            logger.info("The current season is over! Looking to next year...")
            del games, stats
            games, stats = HuskerSchedule(year=now_cst.year + 1)
            now_cst_orig = now_cst
            now_cst = datetime(datetime.now().year + 1, 3, 1).astimezone(tz=TZ)

        game_compared = None

        for game in games:
            if opponent:  # Specific team
                if game.opponent.lower() == opponent.lower():
                    game_compared = game
                    break
            elif game.game_date_time > now_cst:  # Next future game
                game_compared = game
                break

        if game_compared is None:
            raise StatsException(
                f"Unable to find the {year} {opponent.capitalize()} game!"
            )

        logger.info(f"Game compared: {game_compared.opponent}")
        del games, opponent, game, stats

        if now_cst_orig:
            dt_game_time_diff = game_compared.game_date_time - now_cst_orig
        else:
            dt_game_time_diff = game_compared.game_date_time - now_cst
        diff_hours_minutes = convert_seconds(
            dt_game_time_diff.seconds
        )  # datetime object does not have hours or minutes
        year_days = 0

        logger.info(f"Time diff: {dt_game_time_diff}")
        logger.info(f"Time diff mins: {diff_hours_minutes}")

        if dt_game_time_diff.days < 0:
            if calendar.isleap(now_cst.year):
                year_days = 366
            else:
                year_days = 365

        days = dt_game_time_diff.days + year_days
        hours = diff_hours_minutes[0]
        minutes = diff_hours_minutes[1]
        opponent = game_compared.opponent
        thumbnail = game_compared.icon
        date_time = game_compared.game_date_time
        consensus = get_consensus_line(
            team_name=game_compared.opponent, year=now_cst.year
        )
        location = game_compared.location

        if date_time.hour == DT_TBA_HR and date_time.minute == DT_TBA_MIN:
            embed = buildEmbed(
                title="Countdown town...",
                thumbnail=thumbnail,
                fields=[
                    dict(name="Opponent", value=opponent),
                    dict(
                        name="Scheduled Time",
                        value=date_time.strftime(DT_OBJ_FORMAT_TBA),
                    ),
                    dict(name="Location", value=location),
                    dict(name="Time Remaining", value=days),
                    dict(
                        name="Betting Info",
                        value=consensus if consensus else "Line TBD",
                    ),
                ],
            )
        else:
            embed = buildEmbed(
                title="Countdown town...",
                thumbnail=thumbnail,
                fields=[
                    dict(name="Opponent", value=opponent),
                    dict(
                        name="Scheduled Time", value=date_time.strftime(DT_OBJ_FORMAT)
                    ),
                    dict(name="Location", value=location),
                    dict(
                        name="Time Remaining",
                        value=f"{days} days, {hours} hours, and {minutes} minutes",
                    ),
                    dict(
                        name="Betting Info",
                        value=consensus if consensus else "Line TBD",
                    ),
                ],
            )

        await interaction.followup.send(embed=embed)
        logger.info(f"Countdown done")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FootballStatsCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
