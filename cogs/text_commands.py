from discord.ext import commands
from config import client
import markovify
import random
import json
import datetime
import pytz
import discord
import requests
import time
import re
import typing

# Dictionaries
eight_ball = ['As I see it, yes','Ask again later','Better not tell you now','Cannot predict now','Coach V\'s cigar would like this','Concentrate and ask again','Definitely yes','Don’t count on it','Frosty','Fuck Iowa','It is certain','It is decidedly so','Most Likely','My reply is no','My sources say no','Outlook not so good, and very doubtful','Reply hazy','Scott Frost approves','These are the affirmative answers.','Try again','Try again','Without a doubt','Yes – definitely','You may rely on it']
husker_schedule = []
globalRate = 3
globalPer = 30


class TextCommands(commands.Cog, name="Text Commands"):
    @commands.command()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def stonk(self, ctx):
        """ Isms hates stocks. """
        await ctx.send("Stonk!")

    @commands.command(aliases=["mkv",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def markov(self, ctx, *what: typing.Union[discord.Member, discord.TextChannel]):
        edit_msg = await ctx.send("Thinking...")
        source_data = ""

        if not what:
            async for msg in ctx.message.channel.history(limit=5000):
                if msg.content != "" and not msg.author.bot:
                    source_data += "\r\n" + msg.content
        else:
            bannedchannels = ["test-banned", "news-politics", "huskerchat"]

            if len(what) > 5:
                await edit_msg.edit(content="...this might take awhile...be patient...")

            f = open("scofro.txt", "r")
            scottFrost = ""

            for source in what:
                if type(source) == discord.Member:
                    if source.bot:
                        if f.mode == "r":
                            scottFrost += f.read()
                        source_data = re.sub(r'[^\x00-\x7f]', r'', scottFrost)
                    else:
                        async for msg in ctx.channel.history(limit=5000):
                            if msg.content != "" and str(msg.author) == str(source) and not msg.author.bot:
                                source_data += "\r\n" + str(msg.content).capitalize()
                elif type(source) == discord.TextChannel:
                    if source.name not in bannedchannels:
                        async for msg in source.history(limit=5000):
                            if msg.content != "" and not msg.author.bot:
                                source_data += "\r\n" + msg.content

            f.close()

        if not source_data:
            await edit_msg.edit(content="You broke me!")
            return

        chain = markovify.NewlineText(source_data, well_formed=True)
        sentence = chain.make_short_sentence(min_chars=45, max_chars=500)

        if sentence is None:
            await edit_msg.edit(content="You broke me!")
        else:
            await edit_msg.edit(content=sentence)

    @commands.command(aliases=["cd",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def countdown(self, ctx, *, input=None):
        """ Returns the time until the next game if no input is provide or returns time to a specific game if provided.
        Usage: `$[countdown|cd] [team on current schedule]`
        """
        i = 0
        timezone_cst = "CST6CDT"
        timezone_cst_offset = datetime.timedelta(hours=5)
        opponentsList = {}

        with open('husker_schedule.json', 'r') as fp:  # Open the Husker schedule JSON for use
            huskerSchedule = json.load(fp)
        fp.close()

        for game in huskerSchedule:  # Record an index within huskerSchedule
            if game["home_team"] != "Nebraska":
                opponentsList.update({game["home_team"].lower(): i})
            else:
                opponentsList.update({game["away_team"].lower(): i})
            i += 1

        def cstNow():
            cst_now = pytz.utc.localize(datetime.datetime.utcnow())
            cst_now = cst_now.astimezone(pytz.timezone(timezone_cst))
            return cst_now

        if input:  # $countdown|cd <team>
            try:
                game_index = opponentsList[input.lower()]
            except KeyError:
                await ctx.send("__[{}]__ does not exist on the current schedule. Please review `$schedule` and try again.".format(input.title()))
                return

            gameDT = datetime.datetime.strptime(huskerSchedule[game_index]['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            gameDT = pytz.utc.localize(gameDT)

            totalRemaining = gameDT - cstNow()
            hrs = int(totalRemaining.seconds / 3600)
            min = int((totalRemaining.seconds / 60) % 60)

            # CollegeFootballData API stores game with no set time as hour 4 or 5
            print("gameDT.hour == {}".format(gameDT.hour))
            if gameDT.hour == 4 or gameDT.hour == 5:
                gameDT -= timezone_cst_offset
                await ctx.send("📢 📅 There is __[{} days, {} hours, and {} minutes]__ until the game kicks off against __[{}]__ at __[{}]__!".format(
                    totalRemaining.days,
                    hrs,
                    min,
                    input.title(),
                    gameDT.strftime("%x")
                ))
            else:
                gameDT -= timezone_cst_offset
                await ctx.send("📢 📅 There is __[{} days, {} hours, and {} minutes]__ until the game kicks off against __[{}]__ at __[{} CST/CDT]__!".format(
                    totalRemaining.days,
                    hrs,
                    min,
                    input.title(),
                    gameDT.strftime("%x %X")
                ))
        else:  # $countdown|cd
            for game in huskerSchedule:
                gameDT = datetime.datetime.strptime(game['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                gameDT = pytz.utc.localize(gameDT)

                if cstNow() < gameDT:
                    totalRemaining = gameDT - cstNow()
                    hrs = int(totalRemaining.seconds / 3600)
                    min = int((totalRemaining.seconds / 60) % 60)

                    if game["home_team"] == "Nebraska":
                        opponentName = game["away_team"]
                    else:
                        opponentName = game["home_team"]

                    gameDT -= timezone_cst_offset
                    await ctx.send("📢 📅 There is __[{} days, {} hours, and {} minutes]__ until the game kicks off against __[{}]__ at __[{} CST/CDT]__!".format(
                        totalRemaining.days,
                        hrs,
                        min,
                        opponentName.title(),
                        gameDT.strftime("%x %X")
                    ))
                    break

    @commands.command(aliases=["bf", "facts",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def billyfacts(self, ctx):
        """ Real facts about Bill Callahan. """
        msg = await ctx.send("Loading...")

        facts = []
        with open("facts.txt") as f:
            for line in f:
                facts.append(line)
        f.close()

        random.shuffle(facts)
        await msg.edit(content=random.choice(facts))

    @commands.command(aliases=["8b",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def eightball(self, ctx):
        """ Ask a Magic 8-Ball a question. """
        random.shuffle(eight_ball)
        dice_roll = random.randint(0, len(eight_ball) - 1)

        embed = discord.Embed(title="The HuskerBot 8-Ball :8ball: says...", description=eight_ball[dice_roll], color=0xFF0000)
        embed.set_thumbnail(url="https://i.imgur.com/L5Gpu0z.png")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def weather(self, ctx, which="current"):
        """ Checks the weather for game day.
        $weather current  : returns current weather data for the location of Nebraska's next game.
        $weather forecast : returns the current 5 day forecast for the location of Nebraska's next game.
        """

        # Load schedule to get venue
        with open('husker_schedule.json', 'r') as fp:
            husker_sched = json.load(fp)

        venueID = ""
        venueName = ""
        next_game = ""

        for game in husker_sched:
            game_datetime_raw = game['start_date'].split("T")
            game_datetime = datetime.datetime.strptime("{} {}".format(game_datetime_raw[0], game_datetime_raw[1][:-5]), "%Y-%m-%d %H:%M:%S")  # "%b %d, %Y %I:%M %p"
            game_datetime = datetime.datetime(year=game_datetime.year, month=game_datetime.month, day=game_datetime.day, hour=game_datetime.hour, minute=game_datetime.minute, second=game_datetime.second, tzinfo=game_datetime.tzinfo)

            if datetime.datetime.now() < game_datetime:
                venueID = game["venue_id"]
                venueName = game["venue"]
                if game["away_team"] == "Nebraska":
                    next_game = game["home_team"]
                elif game["home_team"] == "Nebraska":
                    next_game = game["away_team"]
                break
            else:
                venueID = None

        if venueID:
            r = requests.get(url="https://api.collegefootballdata.com/venues")
            venue_dict = r.json()

            dump = True
            if dump:
                with open("venue_dict.json", "w") as fp:
                    json.dump(venue_dict, fp, sort_keys=True, indent=4)
                fp.close()

            coords = {}
            for venues in venue_dict:
                if venues["id"] == venueID:
                    coords = venues["location"]
        else:
            await ctx.send("Unable to locate venue.")
            return

        r = requests.get(url="https://api.weatherbit.io/v2.0/current?key={}&lang=en&units=I&lat={}&lon={}".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
        weather_dict = r.json()

        embed = discord.Embed(
            title="Weather Forecast for __[{}]__ in __[{}, {}]__".format(venueName, weather_dict["data"][0]["city_name"], weather_dict["data"][0]["state_code"]),
            color=0xFF0000,
            description="Nebraska's next opponent is __[{}]__".format(next_game))

        if which == "current":
            embed.set_thumbnail(url="https://www.weatherbit.io/static/img/icons/{}.png".format(weather_dict["data"][0]["weather"]["icon"]))
            embed.add_field(name="Temperature", value="{} F".format(weather_dict["data"][0]["temp"]))
            embed.add_field(name="Cloud Coverage", value="{}%".format(weather_dict["data"][0]["clouds"]))
            embed.add_field(name="Wind Speed", value="{} MPH / {}".format(weather_dict["data"][0]["wind_spd"], weather_dict["data"][0]["wind_cdir"]))
            embed.add_field(name="Snow Chance", value="{:.2f}%".format(weather_dict["data"][0]["snow"]))
            embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(weather_dict["data"][0]["precip"]*100))
        elif which == "forecast":
            r = requests.get(url="https://api.weatherbit.io/v2.0/forecast/daily?key={}&lang=en&units=I&lat={}&lon={}&days=7".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = True
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            for days in weather_dict["data"]:
                datetime_obj = datetime.datetime.strptime(days["datetime"], "%Y-%m-%d")
                if datetime_obj.weekday() == 5:
                    embed = discord.Embed(
                        title="Game day forecast for Nebraska's next game at {} in {}, {}".format(venueName, weather_dict["city_name"], weather_dict["state_code"]),
                        color=0xFF0000,
                        description="Nebraska's next game is __[{}]__ supposed to be __[{}]__".format(next_game, days["weather"]["description"]))

                    embed.set_thumbnail(url="https://www.weatherbit.io/static/img/icons/{}.png".format(days["weather"]["icon"]))
                    embed.add_field(name="Temperature", value="{} F".format(days["temp"]))
                    embed.add_field(name="Cloud Coverage", value="{}%".format(days["clouds"]))
                    embed.add_field(name="Wind Speed", value="{} MPH / {}".format(days["wind_spd"], days["wind_cdir"]))
                    embed.add_field(name="Snow Chance", value="{:.2f}%".format(days["snow"]))
                    embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(days["precip"] * 100))
        else:
            await ctx.send("`Current` and `forecast` are the only options for `$weather`. Please try again.")
            return

        embed.set_footer(text="There is a daily 500 call limit to the API used for this command. Do not abuse it.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["gbr",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def balloons(self, ctx):
        balloons = [
            "```\n"
            "🎈🎈🎈🎈  🎈🎈🎈🎈  🎈🎈🎈🎈\n"
            "🎈        🎈   🎈   🎈   🎈\n"
            "🎈  🎈🎈  🎈🎈🎈    🎈🎈🎈\n"
            "🎈    🎈  🎈   🎈   🎈   🎈\n"
            "🎈🎈🎈🎈  🎈🎈🎈🎈  🎈    🎈\n"
            "```"
        ]

        loops = len(balloons)
        i = 0

        msg = await ctx.send(balloons[0])
        while i < loops:
            await msg.edit(content=balloons[i])
            i += 1
            time.sleep(0.5)

    @commands.command(aliases=["24",])
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def _24hours(self, ctx):
        await ctx.send(f"We have 24 hours to celebrate a win or mourn a loss. That time ends in [].")
        pass

    @commands.command()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def userorder(self, ctx, count=10):
        users = client.get_all_members()

        users_sorted = []
        for user in users:
            users_sorted.append([user.name, user.joined_at])

        def sort_second(val):
            return val[1]

        users_sorted.sort(key=sort_second)

        earliest = "```\n"
        for index, user in enumerate(users_sorted):
            if index < count:
                earliest += f"#{index + 1:2}: {user[1]}: {user[0]}\n"
        earliest += "```"
        await ctx.send(earliest)


def setup(bot):
    bot.add_cog(TextCommands(bot))