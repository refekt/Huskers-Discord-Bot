from discord.ext import commands
import markovify
import random
import json
import datetime
import pytz
import discord
import requests
import time
import calendar

# Dictionaries
eight_ball = ['As I see it, yes','Ask again later','Better not tell you now','Cannot predict now','Coach V\'s cigar would like this','Concentrate and ask again','Definitely yes','Don’t count on it','Frosty','Fuck Iowa','It is certain','It is decidedly so','Most Likely','My reply is no','My sources say no','Outlook not so good, and very doubtful','Reply hazy','Scott Frost approves','These are the affirmative answers.','Try again','Try again','Without a doubt','Yes – definitely','You may rely on it']
husker_schedule = []


class TextCommands(commands.Cog, name="Text Commands"):
    # TODO Possibly remove this command.
    @commands.command()
    async def stonk(self, ctx):
        """ Isms hates stocks. """
        await ctx.send("Stonk!")

    # TODO Maybe tweak this to make it a big more realistic.
    @commands.command(aliases=["mkv",])
    async def markov(self, ctx):
        """A Markov chain is a model of some random process that happens over time. Markov chains are called that because they follow a rule called the Markov property. The Markov property says that whatever happens next in a process only depends on how it is right now (the state). It doesn't have a "memory" of how it was before. It is helpful to think of a Markov chain as evolving through discrete steps in time, although the "step" doesn't need to have anything to do with time. """
        source_data=''
        edit_msg = await ctx.send("Thinking...")

        async for msg in ctx.channel.history(limit=5000):
            if msg.content != "":
                    source_data += msg.content + ". "
        source_data.replace("\n", ". ")

        chain = markovify.Text(source_data, well_formed=True)
        sentence = chain.make_sentence(tries=100, max_chars=60, max_overlap_ratio=.78)

        # Get rid of things that would be annoying
        sentence.replace("$","_")
        sentence.replace("@","~")
        sentence.replace("..", ".)")

        await edit_msg.edit(content=sentence)

    @commands.command(aliases=["cd",], brief="How long until Husker football?")
    async def countdown(self, ctx, *, input=None):
        """ Returns the time until the next game if no input is provide or returns time to a specific game if provided.
        Usage: `$[countdown|cd] [team on current schedule]`
        """
        cd_string = ""
        counter = -1
        opponentsDict = {}
        i = 0
        cst_timezone_location = "America/Chicago"
        server_timezone_offset = 1  # Server in EST?

        with open('husker_schedule.json', 'r') as fp:
            husker_sched = json.load(fp)

        if input:
            for game in husker_sched:
                if game["home_team"] != "Nebraska":
                    opponentsDict.update({game["home_team"].lower(): i})
                else:
                    opponentsDict.update({game["away_team"].lower(): i})
                i += 1

            try:
                game_index = opponentsDict[input.lower()]
            except KeyError:
                await ctx.send("`{}` does not exist on the current schedule. Please review `$schedule` and try again.".format(input))
                return

            game_datetime_raw = datetime.datetime.strptime(husker_sched[game_index]['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
            game_datetime_utc = pytz.utc.localize(game_datetime_raw)
            game_datetime_cst = game_datetime_utc.astimezone(pytz.timezone(cst_timezone_location))

            cst_now_raw = pytz.utc.localize(datetime.datetime.utcnow())
            cst_now = cst_now_raw.astimezone(pytz.timezone(cst_timezone_location))

            days_left = game_datetime_cst - cst_now

            if game_datetime_utc.hour == 0 or game_datetime_utc.hour == 4 or game_datetime_utc.hour == 5:
                cd_string = "📢📅 There are __[{} days]__ remaining until the __[{} vs. {}]__ game kicks off on __[{}/{}/{}]__".format(
                    days_left.days,
                    husker_sched[game_index]['home_team'], husker_sched[game_index]['away_team'],
                    game_datetime_cst.month,
                    game_datetime_cst.day,
                    game_datetime_cst.year)
            else:
                cd_string = "📢📅 There are __[{} days, {} hours, and {} minutes]__ remaining until the __[{} vs. {}]__ game kicks off at __[{} CST]__ on __[{}/{}/{}]__".format(
                    days_left.days,
                    int(days_left.seconds / 3600) + server_timezone_offset,
                    int((days_left.seconds / 60) % 60),
                    husker_sched[game_index]['home_team'], husker_sched[game_index]['away_team'],
                    datetime.time(hour=game_datetime_cst.hour, minute=game_datetime_cst.minute),
                    game_datetime_cst.month,
                    game_datetime_cst.day,
                    game_datetime_cst.year)
        else:  # No team provided
            for game in husker_sched:
                game_datetime_raw = datetime.datetime.strptime(game['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                game_datetime_utc = pytz.utc.localize(game_datetime_raw)
                game_datetime_cst = game_datetime_utc.astimezone(pytz.timezone(cst_timezone_location))

                cst_now_raw = pytz.utc.localize(datetime.datetime.utcnow())
                cst_now = cst_now_raw.astimezone(pytz.timezone(cst_timezone_location))

                if cst_now < game_datetime_cst:
                    days_left = game_datetime_cst - cst_now
                    cd_string = "📢📅 There are __[{} days, {} hours, and {} minutes]__ remaining until the __[{} vs. {}]__ game kicks off at __[{} CST]__ on __[{}/{}/{}]__".format(
                        days_left.days,
                        int(days_left.seconds/3600) + server_timezone_offset,
                        int((days_left.seconds / 60) % 60),
                        game['home_team'], game['away_team'],
                        datetime.time(hour=game_datetime_cst.hour, minute=game_datetime_cst.minute),
                        game_datetime_cst.month,
                        game_datetime_cst.day,
                        game_datetime_cst.year)
                    break
                else:
                    cd_string = "Something went wrong 🤫!"

                counter += 1

        await ctx.send(cd_string)

    @commands.command(aliases=["bf", "facts",])
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
    async def eightball(self, ctx, *, question):
        """ Ask a Magic 8-Ball a question. """
        random.shuffle(eight_ball)
        dice_roll = random.randint(0, len(eight_ball))

        embed = discord.Embed(title="The HuskerBot 8-Ball :8ball: says...", description=eight_ball[dice_roll], color=0xFF0000)
        embed.set_thumbnail(url="https://i.imgur.com/L5Gpu0z.png")
        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx, which="current"):
        """ Checks the weather for game day.
        $weather current  : returns current weather data for the location of Nebraska's next game.
        $weather forecast : returns the current 5 day forecast for the location of Nebraska's next game.
        """

        # Load schedule to get venue
        with open('husker_schedule.json', 'r') as fp:
            husker_sched = json.load(fp)

        venue = ""
        next_game = ""

        for game in husker_sched:
            game_datetime_raw = game['start_date'].split("T")
            game_datetime = datetime.datetime.strptime("{} {}".format(game_datetime_raw[0], game_datetime_raw[1][:-5]), "%Y-%m-%d %H:%M:%S")  # "%b %d, %Y %I:%M %p"
            game_datetime = datetime.datetime(year=game_datetime.year, month=game_datetime.month, day=game_datetime.day, hour=game_datetime.hour, minute=game_datetime.minute, second=game_datetime.second, tzinfo=game_datetime.tzinfo)

            if datetime.datetime.now() < game_datetime:
                venue = game["venue"]
                if game["away_team"] == "Nebraska":
                    next_game = game["home_team"]
                elif game["home_team"] == "Nebraska":
                    next_game = game["away_team"]
                break
            else:
                venue = None

        if venue:
            r = requests.get(url="https://api.collegefootballdata.com/venues")
            venue_dict = r.json()

            coords = {}
            for venues in venue_dict:
                if venues["name"] == venue:
                    coords = venues["location"]
        else:
            await ctx.send("Unable to locate venue.")
            return

        sky_description = "Sunny"
        sky_conditions = [
            ("Cloudy", 100),
            ("Mostly Cloudy", (7/8)*100),
            ("Partly Cloudy", (5/8)*100),
            ("Mostly Sunny", (3/8)*100)
        ]

        wind_description = "None"
        wind_conditions = [
            ("Strong Winds", 999),
            ("Very Windy", 40),
            ("Windy", 30),
            ("Breezy", 25),
            ("Light", 5),
            ("Very Light", 1)
        ]

        if which == "current":
            r = requests.get(url="https://api.weatherbit.io/v2.0/current?key={}&lang=en&units=I&lat={}&lon={}".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = False
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            embed = discord.Embed(
                title="Weather Forecast for __[{}]__ in __[{}, {}]__".format(venue, weather_dict["data"][0]["city_name"], weather_dict["data"][0]["state_code"]),
                color=0xFF0000,
                description="Nebraska's next opponent is __[{}]__".format(next_game))
            embed.set_thumbnail(url="https://i.imgur.com/EjAlGCb.png")

            embed.add_field(name="Temperature", value="{} F".format(weather_dict["data"][0]["temp"]))

            for condition in sky_conditions:
                if weather_dict["data"][0]["clouds"] == condition[1]:
                    break
                elif weather_dict["data"][0]["clouds"] > condition[1]:
                    sky_description = condition[0]
            embed.add_field(name="Cloud Coverage", value="{} ({}% )".format(sky_description, weather_dict["data"][0]["clouds"]))

            for condition in wind_conditions:
                if (weather_dict["data"][0]["wind_spd"] * 100) == condition[1]:
                    break
                elif (weather_dict["data"][0]["wind_spd"] * 100) > condition[1]:
                    wind_description = condition[0]
            embed.add_field(name="Wind Speed", value="{} ({} MPH / {})".format(wind_description, weather_dict["data"][0]["wind_spd"], weather_dict["data"][0]["wind_cdir"]))

            embed.add_field(name="Snow Chance", value="{:.2f}%".format(weather_dict["data"][0]["snow"]*100))
            embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(weather_dict["data"][0]["precip"]*100))
        elif which == "forecast":
            r = requests.get(url="https://api.weatherbit.io/v2.0/forecast/daily?key={}&lang=en&units=I&lat={}&lon={}&days=7".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = False
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            embed = discord.Embed(
                title="5 day forecast for Nebraska's next game at {} in {}, {}".format(venue, weather_dict["city_name"], weather_dict["state_code"]),
                color=0xFF0000,
                description="Nebraska's next game is __[{}]__".format(next_game))
            embed.set_thumbnail(url="https://i.imgur.com/EjAlGCb.png")

            for days in weather_dict["data"]:
                datetime_obj = datetime.datetime.strptime(days["datetime"], "%Y-%m-%d")
                print(datetime_obj)

                day_str = "Cloud Coverage: {}%\n" \
                          "Wind: {} MPH {}\n" \
                          "Snow Chance: {:.2f}%\n" \
                          "Precip Chance: {:.2f}%\n" \
                          "High Temp: {} F\n" \
                          "Low Temp: {} F\n".format(days["clouds"], days["wind_spd"], days["wind_cdir"], days["snow"]*100, days["precip"]*100, days["max_temp"], days["min_temp"])
                embed.add_field(name="{}".format("{}, {}/{}/{}".format(calendar.day_name[datetime_obj.weekday()], datetime_obj.day, datetime_obj.month, datetime_obj.year)), value=day_str)
        else:
            await ctx.send("`Current` and `forecast` are the only options for `$weather`. Please try again.")
            return

        embed.set_footer(text="There is a daily 500 call limit to the API used for this command. Do not abuse it.")
        await ctx.send(embed=embed)

        #await ctx.send(ow.get_weather(station))

    @commands.command(aliases=["gbr",])
    async def balloons(self, ctx):
        balloons = [
            "```\n🎈🎈🎈🎈  🎈🎈🎈🎈  🎈🎈🎈🎈\n🎈        🎈    🎈  🎈    🎈\n🎈  🎈🎈  🎈🎈🎈    🎈🎈🎈\n🎈    🎈  🎈    🎈  🎈    🎈\n🎈🎈🎈🎈  🎈🎈🎈🎈  🎈    🎈\n```"
        ]

        loops = len(balloons)
        i = 0

        msg = await ctx.send(balloons[0])
        while i < loops:
            await msg.edit(content=balloons[i])
            i += 1
            time.sleep(0.5)
    # Text commands


def setup(bot):
    bot.add_cog(TextCommands(bot))