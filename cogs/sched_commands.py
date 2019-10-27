# All credit to Jeyrad# #4441
import traceback
import requests
from discord.ext import commands
import datetime
import dateutil.parser
import pytz
import json
import discord

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
globalRate = 3
globalPer = 30


class StatBot(commands.Cog, name="Football Schedules and Scores"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["sched",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def schedule(self, ctx, year=2019):
        """ Returns the Nebraska Huskers football schedule. """

        edit_msg = await ctx.send("Loading...")

        url = "https://api.collegefootballdata.com/games?year={}&seasonType=regular&team=nebraska".format(year)
        print(url)
        try:
            r = requests.get(url)
            schedule_list = r.json() # Actually imports a list
        except:
            await ctx.send("An error occurred retrieving schedule data.")
            return

        dump = True
        if dump:
            with open("husker_schedule.json", "w") as fp:
                json.dump(schedule_list, fp, sort_keys=True, indent=4)
            fp.close()

        embed = discord.Embed(title="{} Husker Schedule".format(year), color=0xFF0000)

        for game in schedule_list:
            game_start_datetime_raw = dateutil.parser.parse(game['start_date'])
            game_start_datetime_raw = game_start_datetime_raw + datetime.timedelta(hours=-5)

            # collegefootballdata.com puts TBD times as 23 or 0. ¯\_(ツ)_/¯
            if game_start_datetime_raw.hour == 23 or game_start_datetime_raw.hour == 0:
                game_info_str = "Week {}\n{}\n{}".format(game["week"], game["venue"], game_start_datetime_raw.strftime("%b %d, %Y TBD"))
            else:
                game_info_str = "Week {}\n{}\n{}".format(game["week"], game["venue"], game_start_datetime_raw.strftime("%b %d, %Y %H:%M %p"))

            name_len = 8

            # Abbreviate team names with two words in it.
            if " " in game["home_team"]:
                home_split = game["home_team"].split(" ")
                home_team = "{}. {}".format(home_split[0][0], home_split[1])
            else:
                home_team = game["home_team"]

            if " " in game["away_team"]:
                away_split = game["away_team"].split(" ")
                away_team = "{}. {}".format(away_split[0][0], away_split[1])
            else:
                away_team = game["away_team"]

            # Truncate the names if they are too long.
            if len(home_team) > name_len:
                home_team = "{}...".format(home_team[:name_len])

            if len(away_team) > name_len:
                away_team = "{}...".format(away_team[:name_len])

            # Add points next to names if they exist
            if game["home_points"]:
                embed.add_field(name="{} ({}) vs {} ({})".format(home_team, game["home_points"], away_team, game["away_points"]), value=game_info_str)
            # No points added
            else:
                embed.add_field(name="{} vs {}".format(home_team, away_team), value=game_info_str)

        embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Nebraska_Cornhuskers_logo.svg/1200px-Nebraska_Cornhuskers_logo.svg.png")
        await edit_msg.edit(content="", embed=embed)

    @commands.command()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
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
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
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
