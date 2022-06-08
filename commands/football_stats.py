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
    DT_OBJ_FORMAT,
    DT_OBJ_FORMAT_TBA,
    DT_TBA_HR,
    DT_TBA_MIN,
    GUILD_PROD,
    TZ,
)
from helpers.embed import buildEmbed, collectScheduleEmbeds
from objects.Exceptions import StatsException
from objects.Paginator import EmbedPaginatorView
from objects.Schedule import HuskerSchedule
from objects.Winsipedia import CompareWinsipedia

logger = logging.getLogger(__name__)


cfbd_config = Configuration()
cfbd_config.api_key["Authorization"] = CFBD_KEY
cfbd_config.api_key_prefix["Authorization"] = "Bearer"

__all__ = ["FootballStatsCog"]


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
        games = api.get_games(
            year=year, team="nebraska"
        )  # We only care about Nebraska's schedule
    except ApiException:
        logger.exception("CFBD API unable to get games", exc_info=True)
        raise StatsException("CFBD API unable to get games")

    for index, game in enumerate(games):
        logger.info(f"Checking the Week {game.week} game.")
        if team.lower() == "nebraska":
            if game.week == games[1].week:  # Week 0 game
                return 0

            if not (game.away_points and game.home_points):
                return game.week
            else:
                logger.exception(
                    "Unknown error occured when getting week for Nebraska game",
                    exc_info=True,
                )
        elif (
            game.away_team.lower() == "nebraska" or game.home_team.lower() == "nebraska"
        ) and (
            game.away_team.lower() == team.lower()
            or game.home_team.lower() == team.lower()
        ):
            return game.week

    logger.exception(f"Unable to find week for {team}")
    raise StatsException(f"Unable to find week for {team}")


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

    logger.info(f"Results: {api_response}")

    try:
        lines = None  # Hard code Week 0
        # if len(api_response) > 1:
        #     for game in api_response:
        #         if game.away_team == "Nebraska":
        #             lines = game.lines[0]
        #             break
        # else:
        #     lines = api_response[0].lines[0]
        #
        # if lines is None:
        #     return None
        for game in api_response:
            if game.away_score is None and game.home_score is None:
                lines = game.lines[0]
                break

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
        return None

    return consensus_line


class FootballStatsCog(commands.Cog, name="Football Stats Commands"):
    @app_commands.command(
        name="countdown", description="Get the time until the next game!"
    )
    @app_commands.describe(
        opponent="Name of opponent to lookup", year="Year of the game to look up"
    )
    @app_commands.guilds(GUILD_PROD)
    async def countdown(
        self,
        interaction: discord.Interaction,
        opponent: str = None,
        year: int = datetime.now().year,
    ) -> None:
        logger.info(f"Starting countdown")
        # await interaction.original_message.defer()

        now_cst = datetime.now().astimezone(tz=TZ)
        logger.info(f"Now CST is... {now_cst}")

        games, stats = HuskerSchedule(year=year)

        assert games, StatsException("No games found!")
        # if not games:
        #     raise StatsException("No games found!")

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

        # await interaction.followup.send(embed=embed)
        await interaction.response.send_message(embed=embed)
        logger.info(f"Countdown done")

    @app_commands.command(name="lines", description="Get the betting lines for a game")
    @app_commands.guilds(GUILD_PROD)
    async def lines(
        self,
        interaction: discord.Interaction,
        team_name: str = "Nebraska",
        week: int = None,
        year: int = datetime.now().year,
    ):
        logger.info(f"Gathering info for lines")

        await interaction.response.defer()

        if week is None:
            week = get_current_week(year=year, team=team_name)

        week = 1 if week == 0 else week
        logger.info(f"Current week: {week}")

        games, _ = HuskerSchedule(year=year)
        del _

        lines = None
        icon = None

        for game in games:
            if (
                not team_name.lower() == "nebraska"
                and team_name.lower() == game.opponent.lower()
            ):  # When a team_name is provided
                lines = get_consensus_line(team_name=team_name, year=year, week=week)
                icon = game.icon
                break
            elif (
                game.week == week and game.outcome == ""
            ):  # When a team_name is omitted
                lines = get_consensus_line(team_name=team_name, year=year, week=week)
                icon = game.icon
                break

        lines = "TBD" if lines is None else lines

        embed = buildEmbed(
            title=f"Betting lines for [{team_name.title()}]",
            fields=[
                dict(name="Year", value=f"{year}"),
                dict(name="Week", value=f"{week - 1}"),
                dict(name="Lines", value=lines),
            ],
            thumbnail=icon,
        )

        await interaction.followup.send(embed=embed)
        logger.info(f"Lines completed")

    @app_commands.command(
        name="compare-teams-stats", description="Compare two team's season stats"
    )
    @app_commands.describe(
        team_for="The main team",
        team_against="The team you want to compare the main team against",
    )
    @app_commands.guilds(GUILD_PROD)
    async def compare_team_stats(
        self, interaction: discord.Interaction, team_for: str, team_against: str
    ):
        logger.info(f"Comparing {team_for} against {team_against} stats")
        await interaction.response.defer()

        team_for = team_for.replace(" ", "-")
        team_against = team_against.replace(" ", "-")

        logger.info("Creating a comparison object")
        comparison = CompareWinsipedia(compare=team_for, against=team_against)

        embed = buildEmbed(
            title=f"Historical records for [{team_for.title()}] vs. [{team_against.title()}]",
            inline=False,
            fields=[
                dict(
                    name="Links",
                    value="[All Games ]({comparison.full_games_url}) | "
                    f"[{team_for.title()}'s Games]({'http://www.winsipedia.com/' + team_for.lower()}) |     "
                    f"[{team_against.title()}'s Games]({'http://www.winsipedia.com/' + team_against.lower()})",
                ),
                dict(
                    name=f"{team_for.title()}'s Recoard vs. {team_against.title()}",
                    value=comparison.all_time_record,
                ),
                dict(
                    name=f"{team_for.title()}'s Largest MOV",
                    value=f"{comparison.compare.largest_mov} ({comparison.compare.largest_mov_date})",
                ),
                dict(
                    name=f"{team_for.title()}'s Longest Win Streak",
                    value=f"{comparison.compare.longest_win_streak} ({comparison.compare.largest_win_streak_date})",
                ),
                dict(
                    name=f"{team_against.title()}'s Largest MOV",
                    value=f"{comparison.against.largest_mov} ({comparison.against.largest_mov_date})",
                ),
                dict(
                    name=f"{team_against.title()}'s Longest Win Streak",
                    value=f"{comparison.against.longest_win_streak} ({comparison.against.largest_win_streak_date})",
                ),
            ],
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="team-schedule", description="Retrieve the team's schedule"
    )
    @app_commands.describe(year="The year of the schedule")
    @app_commands.guilds(GUILD_PROD)
    async def taem_schedule(
        self, interaction: discord.Interaction, year: int = datetime.now().year
    ):
        await interaction.response.defer()

        pages = collectScheduleEmbeds(year)
        view = EmbedPaginatorView(
            embeds=pages, original_message=await interaction.original_message()
        )

        await interaction.followup.send(embed=view.initial, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FootballStatsCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
