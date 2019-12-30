import traceback
from datetime import datetime

import dateutil.parser
import discord
import pytz
import requests
from discord.ext import commands

from utils.consts import ScheduleBackup
from utils.consts import _global_per
from utils.consts import _global_rate
from utils.embed import build_embed

leagueDict = {
    'top25': 0,
    'acc': 1,
    'american': 151,
    'big12': 4,
    'b12': 4,
    'big10': 5,
    'b10': 5,
    'sec': 8,
    'pac12': 9,
    'p12': 9,
    'mac': 15,
    'independent': 18
}
cfbWeeks = [
    datetime(2019, 1, 1),
    datetime(2019, 9, 2),
    datetime(2019, 9, 9),
    datetime(2019, 9, 16),
    datetime(2019, 9, 23),
    datetime(2019, 9, 30),
    datetime(2019, 10, 7),
    datetime(2019, 10, 14),
    datetime(2019, 10, 21),
    datetime(2019, 10, 28),
    datetime(2019, 11, 4),
    datetime(2019, 11, 11),
    datetime(2019, 11, 18),
    datetime(2019, 11, 25),
    datetime(2019, 12, 2)
]
nflWeeks = [
    datetime(2019, 1, 1),
    datetime(2019, 9, 11),
    datetime(2019, 9, 18),
    datetime(2019, 9, 25),
    datetime(2019, 10, 2),
    datetime(2019, 10, 9),
    datetime(2019, 10, 16),
    datetime(2019, 10, 23),
    datetime(2019, 10, 30),
    datetime(2019, 10, 6),
    datetime(2019, 11, 13),
    datetime(2019, 11, 20),
    datetime(2019, 11, 27),
    datetime(2019, 12, 4),
    datetime(2019, 12, 11),
    datetime(2019, 12, 18),
    datetime(2019, 12, 25)
]


def hex_to_rgb(hex):
    hex = hex.lstrip("#")
    hlen = len(hex)
    rgb = tuple(int(hex[i:i + hlen // 3], 16) for i in range(0, hlen, int(hlen // 3)))
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    c = discord.Colour.from_rgb(r=r, g=g, b=b)
    return c


class ScheduleCommands(commands.Cog, name="Scheduling Commands"):
    @commands.group(aliases=["sched"])
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def schedule(self, ctx, year=datetime.now().year):
        """ Nebraska's football schedule """
        edit_msg = await ctx.send("Loading...")

        scheduled_games = ScheduleBackup(year=year)
        game_data = []
        nl = "\n"
        title = value = ""
        total_len = 0
        for index, game in enumerate(scheduled_games):
            title = f"Game {index + 1}"
            value = \
                f"{game.opponent + ' (' + game.outcome + ')' + nl if game.outcome else game.opponent + nl}" \
                f"{game.game_date_time.strftime('%b %d %Y @ %I:%M %p') + nl}" \
                f"{game.location[0] + ', ' + game.location[1] + nl}" \
                f"{game.tv_station + nl if game.tv_station else ''}" \
                f"{'[Boxscore](' + game.boxscore_url + ')' + nl if game.boxscore_url else ''}" \
                f"{'[Recap](' + game.recap_url + ')' + nl if game.recap_url else ''}" \
                f"{'[Notes](' + game.notes_url + ')' + nl if game.notes_url else ''}" \
                f"{'[Quotes](' + game.quotes_url + ')' + nl if game.quotes_url else ''}" \
                f"{'[History](' + game.history_url + ')' + nl if game.history_url else ''}" \
                f"{'[Gallery](' + game.gallery_url + ')' + nl if game.gallery_url else ''}"

            total_len += len(title) + len(value)

            game_data.append(
                [
                    title,
                    value
                ]
            )

        embed = build_embed(
                f"Nebraska's {year} Schedule",
            )

        embed_extended = None

        for game in game_data:
            if len(embed) + len(game[0]) + len(game[1]) <= 6000:
                embed.add_field(name=game[0], value=game[1])
            else:
                if embed_extended is None:
                    embed_extended = build_embed(f"Nebraska's {year} Schedule")

                embed_extended.add_field(name=game[0], value=game[1])

        await edit_msg.edit(
            embed=embed,
            content=""
        )

        if embed_extended is not None:
            await ctx.send(embed=embed_extended)

    # @schedule.command()
    # async def week(self, ctx, week: int, **kwargs):
    #     if "year" in kwargs.keys():
    #         year = kwargs["year"]
    #     else:
    #         year = datetime.now().year
    #
    #     game_fields = []
    #     teamsapi = teams_api.TeamsApi()
    #     all_teams_info = teamsapi.get_fbs_teams(year=datetime.now().year)
    #
    #     for game in Schedule(year=year):
    #         if week == game.week:
    #             tm = ""
    #             team_info = []
    #             if game.home_team == "Nebraska":
    #                 tm = game.away_team
    #             else:
    #                 tm = game.home_team
    #
    #             for team in all_teams_info:
    #                 try:
    #                     if team.school == tm:
    #                         team_info = team
    #                         break
    #                 except KeyError:
    #                     continue
    #
    #             if game.home_points:
    #                 title = f"Week {game.week}: {game.home_team} ({game.home_points}) vs {game.away_team} ({game.away_points})"
    #             else:
    #                 title = f"Week {game.week}: {game.home_team} vs {game.away_team}"
    #
    #             game_dt = dateutil.parser.parse(game.start_date)
    #             game_dt = game_dt.astimezone(tz=pytz.timezone("US/Central"))
    #
    #             if game_dt.hour == 23:
    #                 description = f"{'Conference Game' if game.conference_game else 'Non-Conference'}\n{game_dt.strftime('%x')}\{game.venue}"
    #             else:
    #                 description = f"{'Conference Game' if game.conference_game else 'Non-Conference'}\n{game_dt.strftime('%x %I:%M %p')}\n{game.venue}"
    #             game_fields.append([title, description])
    #
    #             await ctx.send(
    #                 embed=build_embed(
    #                     title=title,
    #                     color=hex_to_rgb(team_info.color),
    #                     thumbnail=team_info.logos[0],
    #                     fields=[["Game Info", description]]
    #                 )
    #             )
    #             break

    @commands.command()
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def cfb(self, ctx, league='top25', week=-1, year=2019):
        """Returns a schedule w/ scores (if in past or in progress) from ESPN for a given league, week and year.
        Usage is: `cfbsched <league> <week> <year>"""

        leagueInt = leagueDict.get(league.lower(), 0)

        if week == -1:
            week = self.getCurrentWeek(cfbWeeks)

        url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard" \
              "?lang=en&region=us&calendartype=blacklist&limit=300&dates={}&seasontype=2&week={}" \
            .format(year, week)

        if leagueInt > 0:
            url += "&groups={}".format(leagueInt)

        try:
            r = requests.get(url)
            sched_json = r.json()
            response = self.build_scoreboard_response(sched_json["events"])
            await ctx.send(response)

        except:
            await ctx.send("An error occurred retrieving schedule data from ESPN.")
            traceback.print_exc()
            return

    @commands.command()
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def nfl(self, ctx, week=-1, year=datetime.now().year):
        """ Returns a schedule w/ scores (if in past or in progress) from ESPN for a given week and year.
        Usage is: `nflsched <week> <year>"""

        if week == -1:
            week = self.getCurrentWeek(nflWeeks)

        url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard" \
              "?lang=en&region=us&calendartype=blacklist&limit=100&dates={}&seasontype=2&week={}" \
            .format(year, week)

        try:
            r = requests.get(url)
            sched_json = r.json()
            response = self.build_scoreboard_response(sched_json["events"])
            await ctx.send(response)

        except:
            await ctx.send("An error occurred retrieving schedule data from ESPN.")
            traceback.print_exc()
            return

    def build_scoreboard_response(self, events):
        if len(events) == 0:
            return "No events appear to be scheduled."

        response = '```prolog'
        current_date = ''
        for event in events:
            date_str = event["date"]
            period = event["status"]["period"]
            date = dateutil.parser.parse(date_str)

            # Move timezone to Eastern for ESPN.
            date = date.astimezone(pytz.timezone("America/New_York"))
            # Grab central for display purposes.
            date_central = date.astimezone(pytz.timezone("America/Chicago"))

            # Add day of week header w/ date
            event_day = date.strftime("%A")
            if current_date != event_day:
                if current_date != "":
                    response += "\n"
                current_date = event_day
                response += "\n{} - {}".format(event_day, date.strftime("%#m/%#d"))
                response += "\n-------------------------------------------------"

            game = event["competitions"][0]
            if len(game["broadcasts"]) != 0:
                network = game["broadcasts"][0]["names"][0]
            else:
                network = "TBD"

            home = self.parseTeam(game["competitors"][0], True)
            away = self.parseTeam(game["competitors"][1], False)

            status = " Time TBD"
            if period > 0:
                # Game has started progress. Display scores.
                status_txt = event["status"]["type"]["shortDetail"]
                status = "{:>3}-{:<3}{:<12}".format(away["score"], home["score"], status_txt)
            elif date.hour != 0:
                # ESPN sets their TBD games to midnight Eastern.
                status = "{:>12}".format(date_central.strftime("%#I:%M %p %Z"))

            response += "\n{:<8}{:>10} @ {:<10} {:<7}".format(network, away["name"], home["name"], status)

        response += '\n```'

        return response

    def parseTeam(self, teamJson, isHomeTeam):
        name = teamJson["team"]["abbreviation"]
        is_winner = teamJson.get("winner", False)
        rank = teamJson.get("curatedRank", {'current': 99}).get("current", 99)
        score = teamJson.get("score", 0)
        if is_winner:
            name = name + "*" if isHomeTeam else "*" + name
        if rank <= 25:
            name = "{} {}".format(name if isHomeTeam else rank, rank if isHomeTeam else name)

        return {
            'name': name,
            'is_winner': is_winner,
            'rank': rank,
            'score': score
        }

    def getCurrentWeek(self, weeks):
        cur_time = datetime.now()

        cur_week = len(weeks)
        # Reverse it, we'll compare from oldest to newest to find the current week.
        for week in reversed(weeks):
            if cur_time > week:
                return cur_week
            cur_week = cur_week - 1

        return len(weeks)


def setup(bot):
    bot.add_cog(ScheduleCommands(bot))


print("### Schedule Commands loaded! ###")
