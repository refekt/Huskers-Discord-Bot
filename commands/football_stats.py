import calendar
from datetime import datetime

from cfbd import BettingApi, ApiClient, Configuration
from cfbd.rest import ApiException
from dinteractions_Paginator import Paginator
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import ButtonStyle

from objects.Schedule import HuskerSchedule
from objects.Winsipedia import CompareWinsipedia, TeamStatsWinsipediaTeam
from utilities.constants import TZ, CFBD_KEY
from utilities.constants import guild_id_list
from utilities.embed import build_countdown_embed, build_embed, return_schedule_embeds
from discord_slash.utils.manage_commands import create_option


class FootballStatsCommands(commands.Cog):
    @cog_ext.cog_slash(
        name="countdown",
        description="Countdown to the most current or specific Husker game",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="team",
                description="Name of the opponent you want to search",
                required=False,
                option_type=3
            ),
            create_option(
                name="sport",
                description="The name of the sport. Uses Huskers.com's naming convention",
                required=False,
                option_type=3
            )
        ]
    )
    async def _countdown(self, ctx: SlashContext, team: str = None, sport: str = "football"):
        await ctx.defer()

        def convert_seconds(n):
            secs = n % (24 * 3600)
            hour = secs // 3600
            secs %= 3600
            mins = secs // 60

            return hour, mins

        def get_consensus_line(check_game):
            configuration = Configuration()
            configuration.api_key["Authorization"] = CFBD_KEY
            configuration.api_key_prefix["Authorization"] = "Bearer"

            cfb_api = BettingApi(ApiClient(configuration))

            nebraska_team = "Nebraska"
            year = datetime.now().year

            if check_game.location == "Lincoln, NE":
                home_team = "Nebraska"
                away_team = check_game.opponent
            else:
                home_team = check_game.opponent
                away_team = "Nebraska"

            try:
                api_response = cfb_api.get_lines(team=nebraska_team, year=year, away=away_team, home=home_team)
            except ApiException:
                return None

            try:
                lines = api_response[0].lines[0]
                formattedSpread = spreadOpen = overUnder = overUnderOpen = ""
                if lines.get("formattedSpread", None):
                    formattedSpread = lines.get("formattedSpread")
                if lines.get("spreadOpen", None):
                    spreadOpen = lines.get("spreadOpen")
                if lines.get("overUnder", None):
                    overUnder = lines.get("overUnder")
                if lines.get("overUnderOpen", None):
                    overUnderOpen = lines.get("overUnderOpen")
                new_line = "\n"
                consensus_line = f"{formattedSpread + ' (Opened: ' + spreadOpen + ')' + new_line if formattedSpread else ''}{'Over Under ' + overUnder + ' (Opened: ' + overUnderOpen + ')' if overUnder else ''}"
            except IndexError:
                consensus_line = None

            return consensus_line

        now_cst = datetime.now().astimezone(tz=TZ)

        games, stats = HuskerSchedule(sport=sport, year=now_cst.year)

        if not games:
            return await ctx.send(content="No games found!")

        game_compared = None

        for game in games:
            if team:  # Specific team
                if game.opponent.lower() == team.lower():
                    game_compared = game
                    break
            elif game.game_date_time > now_cst:  # Next future game
                game_compared = game
                break

        del games, sport, team, game, stats

        dt_game_time_diff = game_compared.game_date_time - now_cst
        diff_hours_minutes = convert_seconds(dt_game_time_diff.seconds)  # datetime object does not have hours or minutes

        year_days = 0

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
            consensus=get_consensus_line(game_compared),
            location=game_compared.location
        )
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(
        name="compare",
        description="Compare two teams stats",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="comparison_team",
                option_type=3,
                required=True,
                description="The main team you want to compare stats"
            ),
            create_option(
                name="comparison_against",
                option_type=3,
                required=True,
                description="The team you want to compare stats again"
            )
        ]
    )
    async def _compare(self, ctx: SlashContext, comparison_team: str, comparison_against: str):
        await ctx.defer()

        comparison_team = comparison_team.replace(" ", "-")
        comparison_against = comparison_against.replace(" ", "-")

        comparison = CompareWinsipedia(
            compare=comparison_team,
            against=comparison_against
        )
        embed = build_embed(
            title=f"Historical records for [{comparison_team.title()}] vs. [{comparison_against.title()}]",
            inline=False,
            fields=[
                ["Links", f"[All Games ]({comparison.full_games_url}) | "
                          f"[{comparison_team.title()}'s Games]({'http://www.winsipedia.com/' + comparison_team.lower()}) |     "
                          f"[{comparison_against.title()}'s Games]({'http://www.winsipedia.com/' + comparison_against.lower()})"],
                [f"{comparison_team.title()}'s Recoard vs. {comparison_against.title()}", comparison.all_time_record],
                [f"{comparison_team.title()}'s Largest MOV", f"{comparison.compare.largest_mov} ({comparison.compare.largest_mov_date})"],
                [f"{comparison_team.title()}'s Longest Win Streak", f"{comparison.compare.longest_win_streak} ({comparison.compare.largest_win_streak_date})"],
                [f"{comparison_against.title()}'s Largest MOV", f"{comparison.against.largest_mov} ({comparison.against.largest_mov_date})"],
                [f"{comparison_against.title()}'s Longest Win Streak", f"{comparison.against.longest_win_streak} ({comparison.against.largest_win_streak_date})"]
            ]
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
                description="The year of the schedule you want to search"
            ),
            create_option(
                name="sport",
                required=False,
                option_type=3,
                description="The name of the sport. Uses Huskers.com's naming convention",
            )
        ]
    )
    async def _schedule(self, ctx: SlashContext, year: int = datetime.now().year, sport: str = "football"):
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
            indexStyle=ButtonStyle.gray
        )

    @cog_ext.cog_slash(
        name="teamstats",
        description="Historical stats for a team",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="team_name",
                required=True,
                option_type=3,
                description="Name of the team you want to search for"
            )
        ]
    )
    async def _teamstats(self, ctx: SlashContext, team_name: str):
        await ctx.defer()

        team = TeamStatsWinsipediaTeam(team_name=team_name)

        embed = build_embed(
            title=f"{team_name.title()} Historical Stats",
            fields=[
                ["All Time Record", f"{team.all_time_record} ({team.all_time_record_rank})"],
                ["All Time Wins", f"{team.all_time_wins} ({team.all_time_wins_rank})"],
                ["Bowl Games", f"{team.bowl_games} ({team.bowl_games_rank})"],
                ["Bowl Record", f"{team.bowl_record} ({team.bowl_record_rank})"],
                ["Championships", f"{team.championships} ({team.championships_rank})"],
                ["Conference Championships", f"{team.conf_championships} ({team.conf_championships_rank})"],
                ["Consensus All American", f"{team.conf_championships} ({team.conf_championships_rank})"],
                ["Heisman Winners", f"{team.heisman_winners} ({team.heisman_winners_rank})"],
                ["NFL Draft Picks", f"{team.nfl_draft_picks} ({team.nfl_draft_picks_rank})"],
                ["Weeks in AP Poll", f"{team.week_in_ap_poll} ({team.week_in_ap_poll_rank})"]
            ],
            inline=False
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(FootballStatsCommands(bot))
