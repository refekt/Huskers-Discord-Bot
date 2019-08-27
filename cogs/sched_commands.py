# All credit to Jeyrad# #4441
import traceback
import requests
from discord.ext import commands
import datetime
import dateutil.parser
import pytz

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

# First Day of CFB Week List (Mondays)
cfbWeeks = [
    datetime.datetime(2019, 1, 1),
    datetime.datetime(2019, 9, 2),
    datetime.datetime(2019, 9, 9),
    datetime.datetime(2019, 9, 16),
    datetime.datetime(2019, 9, 23),
    datetime.datetime(2019, 9, 30),
    datetime.datetime(2019, 10, 7),
    datetime.datetime(2019, 10, 14),
    datetime.datetime(2019, 10, 21),
    datetime.datetime(2019, 10, 28),
    datetime.datetime(2019, 11, 4),
    datetime.datetime(2019, 11, 11),
    datetime.datetime(2019, 11, 18),
    datetime.datetime(2019, 11, 25),
    datetime.datetime(2019, 12, 2)
]

# First day of NFL Week List (Wednesdays)
nflWeeks = [
    datetime.datetime(2019, 1, 1),
    datetime.datetime(2019, 9, 11),
    datetime.datetime(2019, 9, 18),
    datetime.datetime(2019, 9, 25),
    datetime.datetime(2019, 10, 2),
    datetime.datetime(2019, 10, 9),
    datetime.datetime(2019, 10, 16),
    datetime.datetime(2019, 10, 23),
    datetime.datetime(2019, 10, 30),
    datetime.datetime(2019, 10, 6),
    datetime.datetime(2019, 11, 13),
    datetime.datetime(2019, 11, 20),
    datetime.datetime(2019, 11, 27),
    datetime.datetime(2019, 12, 4),
    datetime.datetime(2019, 12, 11),
    datetime.datetime(2019, 12, 18),
    datetime.datetime(2019, 12, 25)
]


class StatBot(commands.Cog, name="Football Schedules and Scores"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def cfbsched(self, ctx, league='top25', week=-1, year=2019):
        """ Returns a schedule w/ scores (if in past or in progress) from ESPN for a given league, week and year.
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
    async def nflsched(self, ctx, week=-1, year=2019):
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
        cur_time = datetime.datetime.now()

        cur_week = len(weeks)
        # Reverse it, we'll compare from oldest to newest to find the current week.
        for week in reversed(weeks):
            if cur_time > week:
                return cur_week
            cur_week = cur_week - 1

        return len(weeks)


def setup(bot):
    bot.add_cog(StatBot(bot))
