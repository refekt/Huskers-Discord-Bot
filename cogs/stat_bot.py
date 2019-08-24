import requests
import CFBScrapy as cfb
from discord.ext import commands
import discord
import json
from sportsreference.ncaaf.roster import Roster
import datetime
import dateutil.parser


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
husker_schedule = []
huskerbot_footer="Generated by HuskerBot"

class StatBot(commands.Cog, name="CFB Stats"):
    def __init__(self, bot):
        self.bot = bot
        
    # TODO Not started.
    @commands.command()
    async def stats(self, ctx):  #, year, *, name):
        """ Returns the current season's stats for searched player. """
        await ctx.send("This command is under construction.")

    # TODO Iterate through each poll available, sort it, and spit out in a pretty message.
    @commands.command(aliases=["polls",])
    async def poll(self, ctx, year=2019, week=None, seasonType=None):
        """ Returns current Top 25 ranking from the Coach's Poll, AP Poll, and College Football Playoff ranking. """
        await ctx.send("This command is under construction")
        return

        url = "https://api.collegefootballdata.com/rankings?year={}".format(year)

        if not seasonType:
            url = url + "&seasonType=regular"
        else:
            url = url + "&seasonType=postseason"

        if week:
            url = url + "&week={}".format(week)

        try:
            r = requests.get(url)
            poll_json = r.json()
        except:
            await ctx.send("An error occurred retrieving poll data.")
            return

        dump = False
        if dump:
            with open("cfb_polls.json", "w") as fp:
                json.dump(poll_json, fp, sort_keys=True, indent=4)
            fp.close()

        # The second [0] represents a poll.
        temp_poll = poll_json[0]["polls"][0]["ranks"]

    # TODO Discord 2,000 char limit per message really limits this command. Need to make output more readable.
    # Possibly add ability to filter by offense, defense, special teams, etc.
    @commands.command()
    async def roster(self, ctx, team="NEBRASKA", year=2019):
        """ Returns the current roster.
        $roster nebraska 2018
        $roster purdue 2017"""

        await ctx.send("This command is under construction.")
        return

        edit_msg = await ctx.send("Loading...This may take awhile...")
        cornhuskers = Roster(team=team, year=year, slim=True)  # slime=True only returns player names for each index. slime=False will return a dataframe.

        # Setup currently to only accept slime=True
        if len(cornhuskers.players) > 0:
            embed = discord.Embed(title="{}'s {} Roster".format(team, year), color=0xFF0000)
            plyrs = ""
            for p in cornhuskers.players:
                # This is where slime=False would need to be modified.
                plyrs = plyrs + "{}\n".format(cornhuskers.players[p])
                if len(plyrs) > 999:
                    plyrs = plyrs + "[...]"
                    break
            embed.add_field(name="Players", value=plyrs)

            await edit_msg.edit(content="", embed=embed)
        else:
            await edit_msg.edit(content="No players found for {}".format(cornhuskers._team))

    # TODO [Labels : stats] are misaligned. Also, points are missing. Cleaning up the output. This could maybe replace box score or add reactions to see more detailed stats.
    @commands.command(aliases=["gstats", "gs",])
    async def gamestats(self, ctx, season="regular", year=2018, week=1, *team):
        """ Returns game stats for a completed game. """
        await ctx.send("This command is under construction")
        return

        if week >= 13 and season == "regular":
            await ctx.send("Regular seasons weeks are only 1-12. Please enter a correct week.")
            return

        try:
            t = cfb.get_game_team_stats(year=year, week=week, seasonType=season, team=team)
        except:
            await ctx.send("There are no stats for {}'s Week {} game. Please try again.".format(team, week))
            return

        game_data_str = t.to_json(orient="table")
        game_data = json.loads(game_data_str)

        embed = discord.Embed(title="**{}'s and {}'s Game Stats**".format(game_data['data'][0]['school'], game_data['data'][15]['school']), color=0xFF0000)

        i = 0
        counter = 0
        temp_str = ""
        stat_list = ("Poss. Time", "Interceptions", "Fumbles Lost", "Turnovers", "Total Pen Yd", "YPR", "Rushing Attempts", "Rushing yards", "YPP",
                     "Comp-Att", "TPY", "Total Yards", "4th Down Eff", "3rd Down Eff", "1st Downs")

        while i < 30:
            temp_str = temp_str + "{} : {}\n".format(stat_list[counter], game_data['data'][i]['stat'])

            if i == 14:
                embed.add_field(name="{}".format(game_data['data'][i]['school']), value="{}\n".format(temp_str))
                temp_str = ""
                counter = -1
            elif i == 29:
                embed.add_field(name="{}".format(game_data['data'][i]['school']), value="{}\n".format(temp_str))
                temp_str = ""
                break
            i += 1
            counter += 1

        await ctx.send(embed=embed)

    # TODO This command is depreciated until collegefootballdata.com adds line data prior to the game.
    # @commands.command()
    # async def lines(self, ctx, team, season="regular", year=2019):
    #     url = "https://api.collegefootballdata.com/lines?year={}&seasonType={}&team={}".format(year, season, team)
    #     page = None
    #     lines = []
    #
    #     try:
    #         page = requests.get(headers="", url=url)
    #         lines = page
    #
    #         for key in lines:
    #             print(key)
    #         await ctx.send(page)
    #     except:
    #         print("Error")

    """
    Complete overhaul. Need to determine what stats to output and filterability within command. Discord limiting messages to 2,000 chars
    prevents a lot of work.
    https://api.collegefootballdata.com/games/teams?year=2018&week=8&seasonType=regular&team=nebraska&conference=b1g
    """
    # TODO See above.
    @commands.command()
    async def boxscore(self, ctx):
        """ Returns the box score of the searched for game. """

        await ctx.send("This command is under construction.")
        return

        # boxscore_date = ""
        # if week == 1:
        #     boxscore_date = "2018-09-08"  # South Alabama
        # elif week == 2:
        #     boxscore_date = "2019-09-07"  # Colorado
        # elif week == 3:
        #     boxscore_date = "2019-09-14"  # Northern Illinois
        # elif week == 4:
        #     boxscore_date = "2019-09-21"  # Illinois
        # elif week == 5:
        #     boxscore_date = "2019-09-28"  # Ohio State
        # elif week == 6:
        #     boxscore_date = "2019-10-05"  # Northwestern
        # elif week == 7:
        #     boxscore_date = "2019-10-12"  # Minnesota
        # elif week == 8:
        #     boxscore_date = "2019-10-26"  # Indiana
        # elif week == 9:
        #     boxscore_date = "2019-11-02"  # Purdue
        # elif week == 10:
        #     boxscore_date = "2019-11-16"  # Wisconsin
        # elif week == 11:
        #     boxscore_date = "2019-11-23"  # Maryland
        # elif week == 12:
        #     boxscore_date = "2019-11-29"  # Iowa
        #
        # edit_msg = await ctx.send("Thinking...")
        # game = Boxscore("{}-nebraska".format(boxscore_date))
        #
        # # Game Info
        # vs_str =""
        # if game.winning_name == "Nebraska":
        #     vs_str = "{} vs {}".format(game.winning_name, game.losing_name)
        # else:
        #     vs_str = "{} vs {}".format(game.losing_name, game.winning_name)
        #
        # nebraska_str = ""
        # if game.winning_name == "Nebraska":
        #     nebraska_str = game.winning_name
        # else:
        #     nebraska_str = game.losing_name
        #
        # oppo_str = ""
        # if game.winning_name != "Nebraska":
        #     oppo_str = game.winning_name
        # else:
        #     oppo_str = game.losing_name
        #
        # embed_game_info = discord.Embed(title="Boxscore for {}".format(vs_str), description="Location: {} | Time: {}".format(game.stadium, game.time), color=0xFF0000)
        #
        #
        # qb_str = ""
        # i = 0
        # for p in game.home_players:
        #     if game.home_players[i].attempted_passes:
        #         qb_str = qb_str + "Name: {}\n" \
        #                           "Pass Yards per Attempt: {}\n" \
        #                           "Passing Completion: {}%\n" \
        #                           "Passing Touchdowns: {}\n" \
        #                           "Passing Yards: {}\n" \
        #                           "Passing Yards per Attempt: {}\n" \
        #                           "Quarterback Rating: {}\n" \
        #                           "Rush Attempts: {}\n" \
        #                           "Rush Touchdowns: {}\n" \
        #                           "Rush Yards: {}\n" \
        #                           "Rush Yards per Attempt: {}\n\n".format(
        #                                                                 game.home_players[i].name,
        #                                                                 game.home_players[i].pass_yards_per_attempt,
        #                                                                 game.home_players[i].passing_completion,
        #                                                                 game.home_players[i].passing_touchdowns,
        #                                                                 game.home_players[i].passing_yards,
        #                                                                 game.home_players[i].passing_yards_per_attempt,
        #                                                                 game.home_players[i].quarterback_rating,
        #                                                                 game.home_players[i].rush_attempts,
        #                                                                 game.home_players[i].rush_touchdowns,
        #                                                                 game.home_players[i].rush_yards,
        #                                                                 game.home_players[i].rush_yards_per_attempt)
        #     i += 1
        #
        # embed_game_info.add_field(name="Players", value=qb_str)
        #
        # # embed_game_info.add_field(name="{} Total Yards".format(nebraska_str), value=game.home_total_yards)
        # # embed_game_info.add_field(name="{} First Downs".format(nebraska_str), value=game.home_first_downs)
        # # embed_game_info.add_field(name="{} Penalties".format(nebraska_str), value="Total: {}\nYards: {}\nPer Penalty Average: {:.2f}".format(game.home_penalties, game.home_yards_from_penalties, game.home_yards_from_penalties/game.home_penalties))
        # # embed_game_info.add_field(name="{} Turnovers".format(nebraska_str), value="Interceptions: {}\nFumbles: {} out of {}".format(game.home_interceptions, game.home_fumbles_lost, game.home_fumbles))
        # # embed_game_info.add_field(name="{} Penalties".format(oppo_str), value="Total: {}\nYards: {}\nPer Penalty Average: {:.2f}".format(game.away_penalties, game.away_yards_from_penalties, game.away_yards_from_penalties / game.away_penalties))
        # # embed_game_info.add_field(name="{} Turnovers".format(oppo_str), value="Interceptions: {}\nFumbles: {} out of {}".format(game.away_interceptions, game.away_fumbles_lost, game.away_fumbles))
        # # embed_game_info.add_field(name="Home Passing", value="Completions: {}\nAttempts: {}\nPassing Yards: {}\nPassing Touchdowns: {}".format(game.home_pass_completions,game.home_pass_attempts, game.home_pass_yards, game.home_pass_touchdowns), inline=False)
        # # embed_game_info.add_field(name="Home Rush", value="Attempts: {}\nYards Per Attempt: {:.2f}\nRushing Touchdowns: {}".format(game.home_rush_attempts, game.home_rush_yards/game.home_rush_attempts, game.home_rush_touchdowns), inline=False)
        #
        # await edit_msg.delete()
        # await ctx.send(embed=embed_game_info)
        #
        # # Away
        # pass

    # TODO Not started. Intention is to output the last few plays of the current Nebraska game.
    # @commands.command()
    # async def lastplays(self, ctx):
    #     pass

    # TODO Huskers.com updated their website and broek this command.
    @commands.command(aliases=["sched",])
    async def schedule(self, ctx, year=2019):
        """ Returns the Nebraska Huskers football schedule. """

        edit_msg = await ctx.send("Loading...")

        url = "https://api.collegefootballdata.com/games?year={}&seasonType=regular&team=nebraska".format(year)
        try:
            r = requests.get(url)
            schedule_list = r.json() # Actually imports a list
        except:
            await ctx.send("An error occurred retrieving poll data.")
            return

        dump = False
        if dump:
            with open("husker_schedule.json", "w") as fp:
                json.dump(schedule_list, fp, sort_keys=True, indent=4)
            fp.close()

        embed = discord.Embed(title="{} Husker Schedule".format(year), color=0xFF0000)
        for game in schedule_list:
            # TODO Change the ISO 8601 format to something easier to read.
            game_start_datetime_raw = dateutil.parser.parse(game['start_date'])
            game_start_datetime_raw = game_start_datetime_raw + datetime.timedelta(hours=-5)
            game_info_str = "Week {}\n{}\n{}".format(game["week"], game["venue"], game_start_datetime_raw.strftime("%b %d, %Y %H:%M %p"))

            home_team = ""
            home_split = []
            away_team = ""
            away_split = []
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

        await edit_msg.edit(content="", embed=embed)



def setup(bot):
    bot.add_cog(StatBot(bot))