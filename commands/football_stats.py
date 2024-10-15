from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import cfbd
import discord
from cfbd import (
    ApiClient,
    Game,
    GamesApi,
    PlayersApi,
    TeamRecord,
)
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from helpers.constants import (
    CFBD_CONFIG,
    DT_CFBD_GAMES,
    DT_CFBD_GAMES_DISPLAY,
    FIELDS_LIMIT,
    GUILD_PROD,
    TZ,
)
from helpers.embed import buildEmbed, collectScheduleEmbeds
from helpers.misc import checkYearValid
from objects.Bets_Stats_Schedule import (
    BetLines,
    BigTenTeams,
    FootballTeam,
    HuskerSched2024,
    buildTeam,
    getConsensusLineByOpponent,
    getHuskerOpponent,
    getNebraskaGameByOpponent,
)
from objects.Exceptions import StatsException, ScheduleException
from objects.Logger import discordLogger, is_debugging
from objects.Paginator import EmbedPaginatorView
from objects.Thread import prettifyTimeDateValue
from objects.Winsipedia import CompareWinsipedia

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

__all__: list[str] = [
    "FootballStatsCog",
    "gen_countdown",
]

season_stats_year_choices: list[Choice] = []
for _ in range(0, FIELDS_LIMIT - 1, 1):
    cur_year: int = datetime.now().year - _
    season_stats_year_choices.append(Choice(name=str(cur_year), value=cur_year))


async def gen_countdown(
    opponent_name: HuskerSched2024 | str,
) -> discord.Embed:
    year: int = datetime.now().year

    assert checkYearValid(year), StatsException(
        f"The provided year is not valid: {year}"
    )

    try:
        game: Game = getNebraskaGameByOpponent(opponent_name=opponent_name)
    except ScheduleException as e:
        raise e

    start_date: datetime = datetime.strptime(
        (
            game.start_date.split("T")[0] + "T17:00:00.000Z"  # 9:00a CST/CDT
            if game.start_time_tbd
            else game.start_date
        ),
        DT_CFBD_GAMES,
    ).astimezone(tz=TZ)

    consensus: BetLines | str = getConsensusLineByOpponent(
        away_team=game.away_team,
        home_team=game.home_team,
    )
    consensus = consensus or "TBD"

    opponent_info: FootballTeam = buildTeam(getHuskerOpponent(game)["id"])
    dt_difference: timedelta = start_date - datetime.now(tz=TZ)

    embed: discord.Embed = buildEmbed(
        title="",
        color=opponent_info.color,
        thumbnail=opponent_info.logo,
        fields=[
            dict(
                name="Opponent",
                value=getHuskerOpponent(game)["opponent_name"].title(),
            ),
            dict(
                name="Scheduled Date & Time",
                value=start_date.strftime(DT_CFBD_GAMES_DISPLAY),
            ),
            dict(name="Location", value=game.venue),
            dict(
                name="Countdown",
                value=prettifyTimeDateValue(dt_difference.total_seconds()),
            ),
            dict(
                name="Betting Info",
                value=str(consensus) if consensus else "Line TBD",
            ),
        ],
    )
    if game.start_time_tbd:
        embed.set_footer(
            text="Note: Times are set to 11:00 A.M. Central until the API is updated."
        )

    logger.info("Countdown embed creation done")

    return embed


class FootballStatsCog(commands.Cog, name="Football Stats Commands"):
    @app_commands.command(
        name="countdown", description="Get the time until the next game!"
    )
    @app_commands.describe(
        opponent_name="Name of opponent_name to lookup",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def countdown(
        self,
        interaction,  #: discord.Interaction,
        opponent_name: HuskerSched2024,
    ) -> None:
        # logger.info(f"Starting countdown")
        # await interaction.response.defer()
        #
        # year: int = datetime.now().year
        #
        # assert checkYearValid(year), StatsException(
        #     f"The provided year is not valid: {year}"
        # )
        #
        # try:
        #     game: Game = getNebraskaGameByOpponent(opponent_name=opponent_name)
        # except ScheduleException as e:
        #     raise e
        #
        # start_date: datetime = datetime.strptime(
        #     game.start_date.split("T")[0] + "T17:00:00.000Z"  # 9:00a CST/CDT
        #     if game.start_time_tbd
        #     else game.start_date,
        #     DT_CFBD_GAMES,
        # ).astimezone(tz=TZ)
        #
        # consensus: BetLines | str = getConsensusLineByOpponent(
        #     away_team=game.away_team,
        #     home_team=game.home_team,
        # )
        # consensus = consensus or "TBD"
        #
        # opponent_info: FootballTeam = buildTeam(getHuskerOpponent(game)["id"])
        # dt_difference: timedelta = start_date - datetime.now(tz=TZ)
        #
        # embed: discord.Embed = buildEmbed(
        #     title="",
        #     color=opponent_info.color,
        #     thumbnail=opponent_info.logo,
        #     fields=[
        #         dict(
        #             name="Opponent",
        #             value=getHuskerOpponent(game)["opponent_name"].title(),
        #         ),
        #         dict(
        #             name="Scheduled Date & Time",
        #             value=start_date.strftime(DT_CFBD_GAMES_DISPLAY),
        #         ),
        #         dict(name="Location", value=game.venue),
        #         dict(
        #             name="Countdown",
        #             value=prettifyTimeDateValue(dt_difference.total_seconds()),
        #         ),
        #         dict(
        #             name="Betting Info",
        #             value=str(consensus) if consensus else "Line TBD",
        #         ),
        #     ],
        # )
        # if game.start_time_tbd:
        #     embed.set_footer(
        #         text="Note: Times are set to 11:00 A.M. Central until the API is updated."
        #     )
        #
        # await interaction.followup.send(embed=embed)
        # logger.info(f"Countdown done")

        await interaction.response.defer()

        embed: discord.Embed = await gen_countdown(opponent_name)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="lines", description="Get the betting lines for a game")
    @app_commands.describe(
        opponent_name="Name of the opponent_name you want to look up lines for",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def lines(
        self,
        interaction: discord.Interaction,
        opponent_name: HuskerSched2024,
    ) -> None:
        logger.info("Gathering info for lines")

        await interaction.response.defer()

        year: int = datetime.now().year

        assert checkYearValid(year), StatsException(
            f"The provided year is not valid: {year}"
        )

        game: Game = getNebraskaGameByOpponent(opponent_name=opponent_name.lower())
        opponent_info: FootballTeam = buildTeam(getHuskerOpponent(game)["id"])

        consensus: BetLines | str = getConsensusLineByOpponent(
            away_team=game.away_team,
            home_team=game.home_team,
        )
        consensus = consensus or "TBD"

        embed: discord.Embed = buildEmbed(
            title="Opponent Betting Lines",
            fields=[
                dict(name="Opponent Name", value=opponent_name.title()),
                dict(
                    name="Conference/Division",
                    value=f"{opponent_info.conference}/{opponent_info.division}",
                ),
                dict(name="Year", value=f"{year}"),
                dict(name="Week", value=f"{game.week}"),
                dict(name="Lines", value=str(consensus)),
            ],
            thumbnail=opponent_info.logo,
        )

        await interaction.followup.send(embed=embed)
        logger.info("Lines completed")

    @app_commands.command(
        name="compare-teams-stats", description="Compare two team's season stats"
    )
    @app_commands.describe(
        team_for="The main team",
        team_against="The team you want to compare the main team against",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def compare_team_stats(
        self, interaction: discord.Interaction, team_for: str, team_against: str
    ) -> None:
        logger.info(f"Comparing {team_for} against {team_against} stats")
        await interaction.response.defer()

        team_for: str = team_for.replace(" ", "-")
        team_against: str = team_against.replace(" ", "-")

        logger.info("Creating a comparison object")
        comparison: CompareWinsipedia = CompareWinsipedia(
            compare=team_for, against=team_against
        )

        embed: discord.Embed = buildEmbed(
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
                    name=f"{team_for.title()}'s Record vs. {team_against.title()}",
                    value=comparison.all_time_record,
                ),
                dict(
                    name=f"{team_for.title()}'s Largest MOV",
                    value=f"{comparison.compare.largest_mov} ({comparison.compare.largest_mov_date})",
                ),
                dict(
                    name=f"{team_for.title()}'s Longest Win Streak",
                    value=f"{comparison.compare.longest_win_streak} ({comparison.compare.longest_win_streak_date})",
                ),
                dict(
                    name=f"{team_against.title()}'s Largest MOV",
                    value=f"{comparison.against.largest_mov} ({comparison.against.largest_mov_date})",
                ),
                dict(
                    name=f"{team_against.title()}'s Longest Win Streak",
                    value=f"{comparison.against.longest_win_streak} ({comparison.against.longest_win_streak_date})",
                ),
            ],
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="schedule", description="Retrieve the team's schedule")
    @app_commands.describe(year="The year of the schedule")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def schedule(
        self, interaction: discord.Interaction, year: int = datetime.now().year
    ) -> None:
        await interaction.response.send_message(
            content="Loading schedule...this may take several seconds...",
        )

        pages: list[discord.Embed] = collectScheduleEmbeds(year=year)

        if len(pages) == 0:
            await interaction.edit_original_response(
                content=f"Unable to load the {year} schedule. The API has more than likely not been updated."
            )
            return

        view: EmbedPaginatorView = EmbedPaginatorView(
            embeds=pages, original_message=await interaction.original_response()
        )

        await interaction.edit_original_response(
            content="", embed=view.initial, view=view
        )

    @app_commands.command(
        name="player-stats", description="Display Husker stats for the year"
    )
    @app_commands.describe(
        year="The year you want stats",
        player_name="Full name of the player you want to display",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def player_stats(
        self, interaction: discord.Interaction, year: int, player_name: str
    ) -> None:
        logger.info(f"Starting player stat search for {year} {player_name.upper()}")
        await interaction.response.defer()

        if len(player_name.split(" ")) == 0:
            raise StatsException(
                "A player's first and/or last search_name is required."
            )

        if len(str(year)) == 2:
            year += 2000

        assert checkYearValid(year), StatsException(
            f"The provided year is not valid: {year}"
        )

        logger.debug(f"Searching for {player_name}")
        api: PlayersApi = PlayersApi(ApiClient(CFBD_CONFIG))
        api_player_search_result: list[cfbd.PlayerSearchResult] = api.player_search(
            search_term=player_name,
            year=year,
            team=str(BigTenTeams.Nebraska.value),
        )

        if len(api_player_search_result) == 0:
            raise StatsException(
                f"Unable to find {player_name} on the Huskers. Please try again!"
            )

        if isinstance(api_player_search_result, list):
            logger.debug("Retrieving list item")  # Only grabbing the Index 0
            api_player_search_result: cfbd.PlayerSearchResult = (
                api_player_search_result[0]
            )

        logger.info(f"Found player {player_name.upper()}")

        api_season_stat_result: list[
            cfbd.PlayerSeasonStat
        ] = api.get_player_season_stats(
            year=year,
            season_type="both",
            team=BigTenTeams.Nebraska.value,
        )

        if api_season_stat_result:
            logger.info(f"Pulled raw season stats for {player_name.upper()}")
        else:
            raise StatsException(f"Unable to locate stats for {player_name}")

        stat_type_descriptions: dict[str, str] = {
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

        desc: str = (
            f"Position: {api_player_search_result.position}\n"
            f"Height: {int(api_player_search_result.height / 12)}'{api_player_search_result.height % 12}\"\n"
            f"Weight: {api_player_search_result.weight} lbs.\n"
            f"Hometown: {api_player_search_result.hometown}"
        )

        logger.info("Building category embeds")
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
        view: EmbedPaginatorView = EmbedPaginatorView(
            embeds=[embed for embed in stat_categories.values() if embed.fields],
            original_message=await interaction.original_response(),
        )

        await interaction.followup.send(embed=view.initial, view=view)

    # TODO team-stats

    @app_commands.command(name="season-stats", description="The Huskers season stats")
    @app_commands.describe(year="The year you want to see stats")
    @app_commands.choices(
        year_start=season_stats_year_choices, year_end=season_stats_year_choices
    )
    async def season_stats(
        self,
        interaction: discord.Interaction,
        year: int = datetime.now().year,
        year_start: Choice[int] = None,
        year_end: Choice[int] = None,
    ):
        logger.info(f"Retrieving Nebraska's {year} stats")
        await interaction.response.defer(thinking=True)

        if (year_start and year_end is None) or (
            year_start is None and year_end
        ):  # Both variables weren't selected
            logger.exception("Both year_start and year_end were not provided")

            raise StatsException(
                "If you must pick both year start and year end if choosing a date range."
            )

        games_api: GamesApi = GamesApi(ApiClient(CFBD_CONFIG))
        records: list[Optional[TeamRecord]] = []
        total_wins: int = 0
        total_losses: int = 0
        home_wins: int = 0
        home_losses: int = 0
        away_wins: int = 0
        away_losses: int = 0
        conference_wins: int = 0
        conference_losses: int = 0

        if all(
            _ is None for _ in (year_start, year_end)
        ):  # Year provided, but year_start and year_end are None
            logger.info("Generating a single year's stats")

            records = games_api.get_team_records(
                team=BigTenTeams.Nebraska.value, year=year
            )

            assert records, StatsException(
                f"Unable to find records for the Husker's {year} season."
            )

            total_wins = records[0].total["wins"]  # noqa
            total_losses = records[0].total["losses"]  # noqa
            home_wins = records[0].home_games["wins"]  # noqa
            home_losses = records[0].home_games["losses"]  # noqa
            away_wins = records[0].away_games["wins"]  # noqa
            away_losses = records[0].away_games["losses"]  # noqa
            conference_wins = records[0].conference_games["wins"]  # noqa
            conference_losses = records[0].conference_games["losses"]  # noqa
        elif all(
            _ is not None for _ in (year_start, year_end)
        ):  # Both year_start and year_end provided
            logger.info("Generating a range of year's stats")

            for _year in range(  # To prevent year_start and year_end swap
                min(year_start.value, year_end.value),
                max(year_start.value, year_end.value),
            ):
                records = games_api.get_team_records(
                    team=BigTenTeams.Nebraska.value, year=_year
                )

                if records is None:
                    continue

                total_wins += records[0].total["wins"]  # noqa
                total_losses += records[0].total["losses"]  # noqa
                home_wins += records[0].home_games["wins"]  # noqa
                home_losses += records[0].home_games["losses"]  # noqa
                away_wins += records[0].away_games["wins"]  # noqa
                away_losses += records[0].away_games["losses"]  # noqa
                conference_wins += records[0].conference_games["wins"]  # noqa
                conference_losses += records[0].conference_games["losses"]  # noqa

        total_games: int = total_wins + total_losses
        total_away_games: int = away_wins + away_losses
        total_home_games: int = home_wins + home_losses
        total_conference_games: int = conference_wins + conference_losses

        embed: discord.Embed = buildEmbed(
            title=f"Nebraska's {str(year_start.value) + ' to ' + str(year_end.value) if (year_start is not None and year_end is not None) else year} Season Stats",
            fields=[
                dict(
                    name="Wins-Losses",
                    value=f"{total_wins}-{total_losses} ({total_wins / total_games:0.4f})",
                ),
                dict(
                    name="Home Wins-Losses",
                    value=f"{home_wins}-{home_losses} ({home_wins / total_home_games:0.4f})",
                ),
                dict(
                    name="Away Wins-Losses",
                    value=f"{away_wins}-{away_losses} ({away_wins / total_away_games:0.4f})",
                ),
                dict(
                    name="Conference Wins-Losses",
                    value=f"{conference_wins}-{conference_losses} ({conference_wins / total_conference_games:0.4f})",
                ),
            ],
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FootballStatsCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
