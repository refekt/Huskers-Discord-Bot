import calendar
from datetime import datetime

from cfbd import ApiClient, BettingApi, Configuration, GamesApi, StatsApi
from cfbd.rest import ApiException
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_commands import create_option

from objects.Schedule import HuskerSchedule
from objects.Winsipedia import CompareWinsipedia, TeamStatsWinsipediaTeam
from utilities.constants import CFBD_KEY, TZ, guild_id_list, pretty_time_delta
from utilities.embed import build_countdown_embed, build_embed, return_schedule_embeds
import urllib.parse

cfbd_config = Configuration()
cfbd_config.api_key["Authorization"] = CFBD_KEY
cfbd_config.api_key_prefix["Authorization"] = "Bearer"


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Football Stats: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Football Stats: {message}")


def convert_seconds(n):
    secs = n % (24 * 3600)
    hour = secs // 3600
    secs %= 3600
    mins = secs // 60

    return hour, mins


def get_current_week(year: int, team: str) -> int:
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
):
    cfb_api = BettingApi(ApiClient(cfbd_config))

    if week is None:
        week = get_current_week(year=year, team=team_name)

    try:
        api_response = cfb_api.get_lines(team=team_name, year=year, week=week)
    except (ApiException, TypeError):
        return None

    log(f"Results: {api_response}", 1)

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

        log(f"Lines: {lines}", 1)

        formattedSpread = (
            spreadOpen
        ) = overUnder = overUnderOpen = homeMoneyline = awayMoneyline = ""

        if lines.get("formattedSpread", None):
            formattedSpread = lines.get("formattedSpread")
        if lines.get("spreadOpen", None):
            spreadOpen = lines.get("spreadOpen")
        if lines.get("overUnder", None):
            overUnder = lines.get("overUnder")
        if lines.get("overUnderOpen", None):
            overUnderOpen = lines.get("overUnderOpen")
        if lines.get("homeMoneyline", None):
            homeMoneyline = str(lines.get("homeMoneyline"))
        if lines.get("awayMoneyline", None):
            awayMoneyline = str(lines.get("awayMoneyline"))
        new_line = "\n"
        consensus_line = (
            f"{'Spread: ' + formattedSpread + ' (Opened: ' + spreadOpen + ')' + new_line if formattedSpread else ''}"
            f"{'Over/Under:  ' + overUnder + ' (Opened: ' + overUnderOpen + ')' + new_line if overUnder else ''}"
            f"{'Home Moneyline: ' + homeMoneyline + new_line if homeMoneyline else ''}"
            f"{'Away Moneyline: ' + awayMoneyline + new_line if awayMoneyline else ''}"
        )

    except IndexError:
        consensus_line = None

    log(f"Consensus Line: {consensus_line}", 1)

    return consensus_line


class FootballStatsCommands(commands.Cog):
    @cog_ext.cog_slash(
        name="lines",
        description="Get lines for a game",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="week",
                description="Week of the season",
                required=False,
                option_type=4,
            ),
            create_option(
                name="year",
                description="Year of the season",
                required=False,
                option_type=4,
            ),
            create_option(
                name="team_name",
                description="Name of the team in which to get lines",
                required=False,
                option_type=3,
            ),
        ],
    )
    async def _lines(
        self,
        ctx: SlashContext,
        week: int = None,
        team_name: str = "Nebraska",
        year: int = datetime.now().year,
    ):
        log(f"Gathering info for lines", 0)
        games, stats = HuskerSchedule(sport="football", year=year)
        del stats

        lines = None

        if week is None:
            week = get_current_week(year=year, team=team_name)

        week += 1  # account for week 0

        log(f"Current week: {week}", 1)

        icon = None
        for game in games:
            if game.week == week:
                lines = get_consensus_line(
                    team_name=team_name, year=year, week=week - 1
                )
                icon = game.icon
                break

        if lines is None:
            lines = "TBD"

        embed = build_embed(
            title=f"Betting lines for [{team_name.title()}]",
            fields=[["Year", year], ["Week", week - 1], ["Lines", lines]],
            thumbnail=icon,
        )
        await ctx.send(embed=embed)
        log(f"Lines completed", 0)

    @cog_ext.cog_slash(
        name="countdown",
        description="Countdown to the most current or specific Husker game",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="team",
                description="Name of the opponent you want to search",
                required=False,
                option_type=3,
            ),
            create_option(
                name="sport",
                description="The name of the sport. Uses Huskers.com's naming convention",
                required=False,
                option_type=3,
            ),
        ],
    )
    async def _countdown(
        self, ctx: SlashContext, team: str = None, sport: str = "football"
    ):
        log(f"Starting countdown", 0)
        await ctx.defer()

        now_cst = datetime.now().astimezone(tz=TZ)
        log(f"Now CST is... {now_cst}", 1)

        games, stats = HuskerSchedule(sport=sport, year=now_cst.year)

        if not games:
            log("No games found!", 1)
            return await ctx.send(content="No games found!")

        last_game = len(games) - 1
        now_cst_orig = None

        if games[last_game].game_date_time < now_cst:
            log("The current season is over! Looking to next year...", 1)
            del games, stats
            games, stats = HuskerSchedule(sport=sport, year=now_cst.year + 1)
            now_cst_orig = now_cst
            now_cst = datetime(datetime.now().year + 1, 3, 1).astimezone(tz=TZ)

        game_compared = None

        for game in games:
            if team:  # Specific team
                if game.opponent.lower() == team.lower():
                    game_compared = game
                    break
            elif game.game_date_time > now_cst:  # Next future game
                game_compared = game
                break
        log(f"Game compared: {game_compared.opponent}", 1)
        del games, sport, team, game, stats

        if now_cst_orig:
            dt_game_time_diff = game_compared.game_date_time - now_cst_orig
        else:
            dt_game_time_diff = game_compared.game_date_time - now_cst
        diff_hours_minutes = convert_seconds(
            dt_game_time_diff.seconds
        )  # datetime object does not have hours or minutes
        year_days = 0

        log(f"Time diff: {dt_game_time_diff}", 1)
        log(f"Time diff mins: {diff_hours_minutes}", 1)

        if dt_game_time_diff.days < 0:
            if calendar.isleap(now_cst.year):
                year_days = 366
            else:
                year_days = 365

        embed = build_countdown_embed(
            days=dt_game_time_diff.days + year_days,
            hours=diff_hours_minutes[0],
            minutes=diff_hours_minutes[1],
            opponent=game_compared.opponent,
            thumbnail=game_compared.icon,
            date_time=game_compared.game_date_time,
            consensus=get_consensus_line(
                team_name=game_compared.opponent, year=now_cst.year
            ),
            location=game_compared.location,
        )
        await ctx.send(embed=embed)
        log(f"Countdown done", 0)

    @cog_ext.cog_slash(
        name="compare",
        description="Compare two teams stats",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="comparison_team",
                option_type=3,
                required=True,
                description="The main team you want to compare stats",
            ),
            create_option(
                name="comparison_against",
                option_type=3,
                required=True,
                description="The team you want to compare stats again",
            ),
        ],
    )
    async def _compare(
        self, ctx: SlashContext, comparison_team: str, comparison_against: str
    ):
        await ctx.defer()

        comparison_team = comparison_team.replace(" ", "-")
        comparison_against = comparison_against.replace(" ", "-")

        comparison = CompareWinsipedia(
            compare=comparison_team, against=comparison_against
        )
        embed = build_embed(
            title=f"Historical records for [{comparison_team.title()}] vs. [{comparison_against.title()}]",
            inline=False,
            fields=[
                [
                    "Links",
                    f"[All Games ]({comparison.full_games_url}) | "
                    f"[{comparison_team.title()}'s Games]({'http://www.winsipedia.com/' + comparison_team.lower()}) |     "
                    f"[{comparison_against.title()}'s Games]({'http://www.winsipedia.com/' + comparison_against.lower()})",
                ],
                [
                    f"{comparison_team.title()}'s Recoard vs. {comparison_against.title()}",
                    comparison.all_time_record,
                ],
                [
                    f"{comparison_team.title()}'s Largest MOV",
                    f"{comparison.compare.largest_mov} ({comparison.compare.largest_mov_date})",
                ],
                [
                    f"{comparison_team.title()}'s Longest Win Streak",
                    f"{comparison.compare.longest_win_streak} ({comparison.compare.largest_win_streak_date})",
                ],
                [
                    f"{comparison_against.title()}'s Largest MOV",
                    f"{comparison.against.largest_mov} ({comparison.against.largest_mov_date})",
                ],
                [
                    f"{comparison_against.title()}'s Longest Win Streak",
                    f"{comparison.against.longest_win_streak} ({comparison.against.largest_win_streak_date})",
                ],
            ],
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="schedule",
        description="Husker schedule",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="year",
                required=False,
                option_type=4,
                description="The year of the schedule you want to search",
            ),
            create_option(
                name="sport",
                required=False,
                option_type=3,
                description="The name of the sport. Uses Huskers.com's naming convention",
            ),
        ],
    )
    async def _schedule(
        self,
        ctx: SlashContext,
        year: int = datetime.now().year,
        sport: str = "football",
    ):
        await ctx.defer()

        pages = return_schedule_embeds(year, sport=sport)
        await Paginator(
            bot=ctx.bot,
            ctx=ctx,
            pages=pages,
            useIndexButton=True,
            firstStyle=ButtonStyle.gray,
            nextStyle=ButtonStyle.gray,
            prevStyle=ButtonStyle.gray,
            lastStyle=ButtonStyle.gray,
            indexStyle=ButtonStyle.gray,
        ).run()

    @cog_ext.cog_slash(
        name="teamstats",
        description="Historical stats for a team",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="team_name",
                required=True,
                option_type=3,
                description="Name of the team you want to search",
            )
        ],
    )
    async def _teamstats(self, ctx: SlashContext, team_name: str):
        await ctx.defer()

        team = TeamStatsWinsipediaTeam(team_name=team_name)

        embed = build_embed(
            title=f"{team_name.title()} Historical Stats",
            fields=[
                [
                    "All Time Record",
                    f"{team.all_time_record} ({team.all_time_record_rank})",
                ],
                ["All Time Wins", f"{team.all_time_wins} ({team.all_time_wins_rank})"],
                ["Bowl Games", f"{team.bowl_games} ({team.bowl_games_rank})"],
                ["Bowl Record", f"{team.bowl_record} ({team.bowl_record_rank})"],
                ["Championships", f"{team.championships} ({team.championships_rank})"],
                [
                    "Conference Championships",
                    f"{team.conf_championships} ({team.conf_championships_rank})",
                ],
                [
                    "Consensus All American",
                    f"{team.conf_championships} ({team.conf_championships_rank})",
                ],
                [
                    "Heisman Winners",
                    f"{team.heisman_winners} ({team.heisman_winners_rank})",
                ],
                [
                    "NFL Draft Picks",
                    f"{team.nfl_draft_picks} ({team.nfl_draft_picks_rank})",
                ],
                [
                    "Weeks in AP Poll",
                    f"{team.week_in_ap_poll} ({team.week_in_ap_poll_rank})",
                ],
            ],
            inline=False,
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="seasonstats",
        description="Season stats for a team",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="team_name",
                required=False,
                option_type=3,
                description="Name of the team you want to search",
            ),
            create_option(
                name="year",
                required=False,
                option_type=4,
                description="Year of the season you want to search",
            ),
        ],
    )
    async def _seasonstats(
        self,
        ctx: SlashContext,
        team_name: str = "Nebraska",
        year: int = datetime.now().year,
    ):
        cfb_api = StatsApi(ApiClient(cfbd_config))

        try:
            api_response = cfb_api.get_team_season_stats_with_http_info(
                year=year, team=team_name
            )
        except ApiException:
            return None

        season_stats = {}
        for stat in api_response[0]:
            season_stats[stat.stat_name] = stat.stat_value

        pages = [
            # Offense
            build_embed(
                fields=[
                    [
                        "Offense",
                        f"**Total Yards**: {season_stats.get('totalYards', 0):,}\n"
                        f"---\n"
                        f"**Rushing Attempts**: {season_stats.get('rushingAttempts', 0):,}\n"
                        f"**Rushing Yards**: {season_stats.get('rushingYards', 0):,}\n"
                        f"**Rushing TDs**: {season_stats.get('rushingTDs', 0)}\n"
                        f"---\n"
                        f"**Pass Attempts**: {season_stats.get('passAttempts', 0):,}\n"
                        f"**Pass Completions**: {season_stats.get('passCompletions', 0):,}\n"
                        f"**Passing Yards**: {season_stats.get('netPassingYards', 0):,}\n"
                        f"**Passing TDs**: {season_stats.get('passingTDs', 0)}\n"
                        f"---\n"
                        f"**First Downs**: {season_stats.get('firstDowns', 0):,}\n"
                        f"**Third Downs**: {season_stats.get('thirdDowns', 0):,}\n"
                        f"**Third Down Conversions**: {season_stats.get('thirdDownConversions', 0):,}\n"
                        f"**Fourth Downs**: {season_stats.get('fourthDowns', 0)}\n"
                        f"**Fourth Down Conversions**: {season_stats.get('fourthDownConversions', 0)}\n"
                        f"---\n"
                        f"**Interceptions Thrown**: {season_stats.get('interceptions', 0)}\n"
                        f"---\n"
                        f"**Time of Possession**: {pretty_time_delta(season_stats.get('possessionTime', 0))}\n",
                    ],
                ],
            ),
            # Defense
            build_embed(
                fields=[
                    [
                        "Defense",
                        f"**Tackles for Loss**: {season_stats.get('tacklesForLoss', 0)}\n"
                        f"**Sacks**: {season_stats.get('sacks', 0)}\n"
                        f"**Passes Intercepted**: {season_stats.get('passesIntercepted', 0)}\n"
                        f"**Interception Yards**: {season_stats.get('interceptionYards', 0)}\n"
                        f"**Interception TDs**: {season_stats.get('interceptionTDs', 0)}\n",
                    ],
                ],
            ),
            # Special Teams
            build_embed(
                fields=[
                    [
                        "Special Teams",
                        f"**Kick Returns**: {season_stats.get('kickReturns', 0)}\n"
                        f"**Kick Return Yards**: {season_stats.get('kickReturnYards', 0):,}\n"
                        f"**Kick Return TDs**: {season_stats.get('kickReturnTDs', 0)}\n"
                        f"---\n"
                        f"**Punt Returns**: {season_stats.get('puntReturns', 0)}\n"
                        f"**Punt Return Yards**: {season_stats.get('puntReturnYards', 0):,}\n"
                        f"**Punt Return TDs**: {season_stats.get('puntReturnTDs', 0)}\n",
                    ],
                ],
            ),
            # Penalties
            build_embed(
                fields=[
                    [
                        "Penalties",
                        f"**Penalties**: {season_stats.get('penalties', 0)}\n"
                        f"**Penalty Yards**: {season_stats.get('penaltyYards', 0):,}\n",
                    ],
                ],
            ),
            # Fumbles and Turnovers
            build_embed(
                fields=[
                    [
                        "Fumbles and Turnovers",
                        f"**Fumbles Lost**: {season_stats.get('fumblesLost', 0)}\n"
                        f"**Fumbles Recovered**: {season_stats.get('fumblesRecovered', 0)}\n"
                        f"**Turnovers**: {season_stats.get('turnovers', 0)}\n",
                    ],
                ],
            ),
        ]

        content = [
            f"{team_name.title()}'s {year} Offensive Stats",
            f"{team_name.title()}'s {year} Defensive Stats",
            f"{team_name.title()}'s {year} Special Teams Stats",
            f"{team_name.title()}'s {year} Penalties Stats",
            f"{team_name.title()}'s {year} Fumble and Turnover Stats",
        ]

        await Paginator(
            bot=ctx.bot,
            ctx=ctx,
            pages=pages,
            content=content,
            useIndexButton=True,
            useSelect=False,
            firstStyle=ButtonStyle.gray,
            nextStyle=ButtonStyle.gray,
            prevStyle=ButtonStyle.gray,
            lastStyle=ButtonStyle.gray,
            indexStyle=ButtonStyle.gray,
        ).run()


def setup(bot):
    bot.add_cog(FootballStatsCommands(bot))
