import traceback
from datetime import datetime

import dateutil.parser
import discord
import pytz
import requests
from discord.ext import commands

from utils.consts import CD_GLOBAL_RATE, CD_GLOBAL_PER, CD_GLOBAL_TYPE
from utils.embed import build_schedule_embed

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
    datetime(datetime.now().year, 9, 5),
    datetime(datetime.now().year, 9, 12),
    datetime(datetime.now().year, 9, 19),
    datetime(datetime.now().year, 9, 26),
    datetime(datetime.now().year, 10, 3),
    datetime(datetime.now().year, 10, 10),
    datetime(datetime.now().year, 10, 17),
    datetime(datetime.now().year, 10, 24),
    datetime(datetime.now().year, 10, 31),
    datetime(datetime.now().year, 11, 7),
    datetime(datetime.now().year, 11, 14),
    datetime(datetime.now().year, 11, 21),
    datetime(datetime.now().year, 11, 28),
    datetime(datetime.now().year, 12, 5),
    datetime(datetime.now().year, 12, 12),
    datetime(datetime.now().year, 12, 19)
]
nflWeeks = [
    datetime(datetime.now().year, 9, 13),
    datetime(datetime.now().year, 9, 20),
    datetime(datetime.now().year, 9, 27),
    datetime(datetime.now().year, 10, 4),
    datetime(datetime.now().year, 10, 11),
    datetime(datetime.now().year, 10, 18),
    datetime(datetime.now().year, 10, 25),
    datetime(datetime.now().year, 11, 1),
    datetime(datetime.now().year, 11, 8),
    datetime(datetime.now().year, 11, 15),
    datetime(datetime.now().year, 11, 22),
    datetime(datetime.now().year, 11, 29),
    datetime(datetime.now().year, 12, 6),
    datetime(datetime.now().year, 12, 13),
    datetime(datetime.now().year, 12, 20),
    datetime(datetime.now().year, 12, 27),
    datetime(datetime.now().year + 1, 1, 3)
]


def hex_to_rgb(_hex):
    new_hex = _hex.lstrip("#")
    hlen = len(new_hex)
    rgb = tuple(int(new_hex[i:i + hlen // 3], 16) for i in range(0, hlen, int(hlen // 3)))
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    c = discord.Colour.from_rgb(r=r, g=g, b=b)
    return c


class ScheduleCommands(commands.Cog, name="Scheduling Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["sched"])
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def schedule(self, ctx):
        """ [year|week] Nebraska's football schedule """
        if not ctx.invoked_subcommand:
            raise AttributeError(f"Missing a subcommand. Review '{self.bot.command_prefix}help {ctx.command.qualified_name}' to view subcommands.")

    @schedule.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def year(self, ctx, year=datetime.now().year):
        """ Specific year of Nebraska's football schedule """
        edit_msg = await ctx.send("Loading...")
        await edit_msg.edit(content="", embed=build_schedule_embed(year))

    @schedule.command()
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def week(self, ctx, which_week, which_year=datetime.now().year):
        """ Specific week in a specific year of Nebraska's schedule"""
        edit_msg = await ctx.send("Loading...")

        await edit_msg.edit(content="", embed=build_schedule_embed(which_year, week=which_week))

    @commands.command()  ## Jeyrad's code ###
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def cfb(self, ctx, league='top25', week=-1, year=datetime.now().year):
        """Returns a schedule w/ scores (if in past or in progress) from ESPN for a given league, week and year.
        Usage is: `cfbsched <league> <week> <year>"""

        leagueInt = leagueDict.get(league.lower(), 0)

        if week == -1:
            week = self.getCurrentWeek(cfbWeeks)

        url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard" \
              f"?lang=en&region=us&calendartype=blacklist&limit=300&dates={year}&seasontype=2&week={week}"

        if leagueInt > 0:
            url += f"&groups={leagueInt}"

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
    @commands.cooldown(rate=CD_GLOBAL_RATE, per=CD_GLOBAL_PER, type=CD_GLOBAL_TYPE)
    async def nfl(self, ctx, week=-1, year=datetime.now().year):
        """ Returns a schedule w/ scores (if in past or in progress) from ESPN for a given week and year.
        Usage is: `nflsched <week> <year>"""

        if week == -1:
            week = self.getCurrentWeek(nflWeeks)

        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?lang=en&region=us&calendartype=blacklist&limit=100&dates={year}&seasontype=2&week={week}"

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
                response += f"\n{event_day} - {date.strftime('%#m/%#d')}"
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
                status = f"{away['score']:>3}-{home['score']:<3}{status_txt:<12}"
            elif date.hour != 0:
                # ESPN sets their TBD games to midnight Eastern.
                status = f"{date_central.strftime('%#I:%M %p %Z'):>12}"

            response += f"\n{network:<8}{away['name']:>10} @ {home['name']:<10} {status:<7}"

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
            name = f"{name if isHomeTeam else rank} {rank if isHomeTeam else name}"

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
    ### Jeyrad's code ###


def setup(bot):
    bot.add_cog(ScheduleCommands(bot))

# print("### Schedule Commands loaded! ###")
