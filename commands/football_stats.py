import calendar
from datetime import datetime
from typing import Union, Any, Optional

import cfbd
import discord
from cfbd import (
    ApiClient,
    PlayersApi,
)
from discord import app_commands
from discord.ext import commands

from helpers.betting import get_consensus_line, get_current_week, cfbd_config
from helpers.constants import (
    DT_OBJ_FORMAT,
    DT_OBJ_FORMAT_TBA,
    DT_TBA_HR,
    DT_TBA_MIN,
    GUILD_PROD,
    TZ,
)
from helpers.embed import buildEmbed, collectScheduleEmbeds
from helpers.misc import checkYearValid
from objects.Exceptions import StatsException
from objects.Logger import discordLogger
from objects.Paginator import EmbedPaginatorView
from objects.Schedule import HuskerSchedule
from objects.Winsipedia import CompareWinsipedia

logger = discordLogger(__name__)

__all__ = ["FootballStatsCog"]


def convert_seconds(n) -> Union[int, Any]:
    logger.info(f"Converting {n:,} seconds to hours and minutes")
    secs = n % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60
    return hour, mins


class FootballStatsCog(commands.Cog, name="Football Stats Commands"):
    @app_commands.command(
        name="countdown", description="Get the time until the next game!"
    )
    @app_commands.describe(
        opponent="Name of opponent to lookup",
    )
    @app_commands.guilds(GUILD_PROD)
    async def countdown(
        self,
        interaction: discord.Interaction,
        opponent: str = None,
    ) -> None:
        logger.info(f"Starting countdown")
        await interaction.response.defer()

        if opponent:
            assert opponent.replace(" ", "").replace("-", "").isalpha(), StatsException(
                "Team names must only contain alphabet letters."
            )

        year = datetime.now().year
        assert checkYearValid(year), StatsException(
            f"The provided year is not valid: {year}"
        )

        now_cst = datetime.now().astimezone(tz=TZ)
        logger.info(f"Now CST is... {now_cst}")

        games, stats = HuskerSchedule(year=year)

        assert games, StatsException("No games found!")

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

        logger.info(f"Found game to compare: {game_compared}")

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
                logger.info("Accounting for leap year")
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
            logger.info("Building a TBA game time embed")
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
            logger.info("Building embed")
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

    @app_commands.command(name="lines", description="Get the betting lines for a game")
    @app_commands.describe(
        team_name="Name of the opponent you want to look up lines for",
    )
    @app_commands.guilds(GUILD_PROD)
    async def lines(
        self,
        interaction: discord.Interaction,
        team_name: str = "Nebraska",
    ) -> None:
        logger.info(f"Gathering info for lines")

        await interaction.response.defer()

        year = datetime.now().year

        assert checkYearValid(year), StatsException(
            f"The provided year is not valid: {year}"
        )

        # if week is None:
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
    ) -> None:
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
                    value=f"[All Games ]({comparison.full_games_url}) | "
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

    @app_commands.command(name="schedule", description="Retrieve the team's schedule")
    @app_commands.describe(year="The year of the schedule")
    @app_commands.guilds(GUILD_PROD)
    async def schedule(
        self, interaction: discord.Interaction, year: int = datetime.now().year
    ) -> None:
        await interaction.response.defer()

        pages = collectScheduleEmbeds(year)
        view = EmbedPaginatorView(
            embeds=pages, original_message=await interaction.original_message()
        )

        await interaction.followup.send(embed=view.initial, view=view)

    @app_commands.command(
        name="player-stats", description="Display players stats for the year"
    )
    @app_commands.describe(
        year="The year you want stats",
        player_name="Full name of the player you want to display",
    )
    @app_commands.guilds(GUILD_PROD)
    async def player_stats(
        self, interaction: discord.Interaction, year: int, player_name: str
    ) -> None:
        logger.info(f"Starting player stat search for {year} {player_name.upper()}")
        await interaction.response.defer()

        if len(player_name.split(" ")) == 0:
            raise StatsException(
                "A player's first and/or last search_name is required."
            )

        assert checkYearValid(year), StatsException(
            f"The provided year is not valid: {year}"
        )

        api = PlayersApi(ApiClient(cfbd_config))
        api_player_search_result: list[cfbd.PlayerSearchResult] = api.player_search(
            search_term=player_name, team="nebraska", year=year
        )

        if not api_player_search_result:
            raise StatsException(f"Unable to find {player_name}. Please try again!")
        api_player_search_result: cfbd.PlayerSearchResult = api_player_search_result[0]
        logger.info(f"Found player {player_name.upper()}")

        api_season_stat_result: list[
            cfbd.PlayerSeasonStat
        ] = api.get_player_season_stats(year=year, team="nebraska", season_type="both")
        logger.info(f"Pulled raw season stats for {player_name.upper()}")

        stat_type_descriptions = {
            "ATT": "Attempts",
            "AVG": "Average",
            "CAR": "Carries",
            "COMPLETIONS": "Completions",
            "FGA": "Field Goals Attempted",
            "FGM": "Field Goals Made",
            "FUM": "Fumbles",
            "INT": "Interceptions",
            "In 20": "Inside 20 Yards",
            "LONG": "Longest",
            "LOST": "Lost",
            "NO": "Number",
            "PCT": "Completion Percent",
            "PD": "Passes Defended",
            "PTS": "Points",
            "QB HUR": "Quarterback Hurries",
            "REC": "Receptions",
            "SACKS": "Sacks",
            "SOLO": "Solo Tackles",
            "TB": "Touchback",
            "TD": "Touchdowns",
            "TFL": "Tackles For Loss",
            "TOT": "Total Tackles",
            "XPA": "Extra Point Attempt",
            "XPM": "Extra Point Made",
            "YDS": "Total Yards",
            "YPA": "Yards Per Attempt",
            "YPC": "Yards Per Carry",
            "YPP": "Yards Per Play",
            "YPR": "Yards Per Reception",
        }

        desc = (
            f"Position: {api_player_search_result.position}\n"
            f"Height: {int(api_player_search_result.height / 12)}'{api_player_search_result.height % 12}\"\n"
            f"Weight: {api_player_search_result.weight} lbs.\n"
            f"Hometown: {api_player_search_result.hometown}"
        )

        logger.info("Building cateorgy embeds")
        stat_categories: dict[str, Optional[discord.Embed]] = {
            "defensive": buildEmbed(
                title=f"{player_name.title()}'s Defense Stats", description=desc
            ),
            "fumbles": buildEmbed(
                title=f"{player_name.title()}'s Fumble Stats", description=desc
            ),
            "interceptions": buildEmbed(
                title=f"{player_name.title()}'s Interception Stats", description=desc
            ),
            "kickReturns": buildEmbed(
                title=f"{player_name.title()}'s Kick Return Stats", description=desc
            ),
            "kicking": buildEmbed(
                title=f"{player_name.title()}'s Kicking Stats", description=desc
            ),
            "passing": buildEmbed(
                title=f"{player_name.title()}'s Passing Stats", description=desc
            ),
            "puntReturns": buildEmbed(
                title=f"{player_name.title()}'s Punt Return Stats", description=desc
            ),
            "punting": buildEmbed(
                title=f"{player_name.title()}'s Punting Stats", description=desc
            ),
            "receiving": buildEmbed(
                title=f"{player_name.title()}'s Receiving Stats", description=desc
            ),
            "rushing": buildEmbed(
                title=f"{player_name.title()}'s Rushing Stats", description=desc
            ),
        }

        logger.info("Updating embeds")
        for stat in api_season_stat_result:
            if (
                not stat.player.lower() == player_name
            ):  # Filter out only the player we're looking for
                continue

            stat_categories[stat.category].add_field(
                name=stat_type_descriptions[stat.stat_type],
                value=str(stat.stat),
                inline=False,
            )

        logger.info("Creating Paginator")
        view = EmbedPaginatorView(
            embeds=[embed for embed in stat_categories.values() if embed.fields],
            original_message=await interaction.original_message(),
        )

        await interaction.followup.send(embed=view.initial, view=view)

    # TODO team-stats

    # TODO season-stats


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FootballStatsCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
