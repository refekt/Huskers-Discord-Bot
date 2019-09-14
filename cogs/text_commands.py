from discord.ext import commands
import markovify
import random
import json
import datetime
import pytz
import discord
import requests
import time

# Dictionaries
eight_ball = ['As I see it, yes','Ask again later','Better not tell you now','Cannot predict now','Coach V\'s cigar would like this','Concentrate and ask again','Definitely yes','Don’t count on it','Frosty','Fuck Iowa','It is certain','It is decidedly so','Most Likely','My reply is no','My sources say no','Outlook not so good, and very doubtful','Reply hazy','Scott Frost approves','These are the affirmative answers.','Try again','Try again','Without a doubt','Yes – definitely','You may rely on it']
husker_schedule = []


class TextCommands(commands.Cog, name="Text Commands"):
    @commands.command()
    async def stonk(self, ctx):
        """ Isms hates stocks. """
        await ctx.send("Stonk!")

    @commands.command(aliases=["cmkv",])
    async def channelmarkov(self, ctx, *, chan: discord.TextChannel):
        """A Markov chain is a model of some random process that happens over time. Markov chains are called that because they follow a rule called the Markov property. The Markov property says that whatever happens next in a process only depends on how it is right now (the state). It doesn't have a "memory" of how it was before. It is helpful to think of a Markov chain as evolving through discrete steps in time, although the "step" doesn't need to have anything to do with time. """
        source_data = ""
        edit_msg = await ctx.send("Thinking...")

        if chan is None:
            embed = discord.Embed(title="You can't do that!", color=0xFF0000)
            embed.set_image(url="http://m.quickmeme.com/img/96/9651e121dac222fdac699ca6d962b84f288c75e6ec120f4a06e3c04f139ee8ec.jpg")
            await edit_msg.edit(content="", embed=embed)
            return

        try:
            async for msg in chan.history(limit=5000):
                if msg.content != "" and not msg.author.bot:
                    source_data += "\r\n" + msg.content
        except:
            await edit_msg.edit(content="You broke me! _(I'm most likely missing permissions for {})_".format(chan))
            return

        if not source_data:
            await edit_msg.edit(content="You broke me! _(Most likely the user hasn't commented in this channel.)_")
            return
        elif len(source_data) < 10:
            await edit_msg.edit(content="Not enough data! Good bye.")
            return

        chain = markovify.NewlineText(source_data, well_formed=True)
        sentence = chain.make_short_sentence(max_chars=300)

        if sentence is None:
            await edit_msg.edit(content="Text channel [{}] does not have enough data. They suck!".format(chan))
        else:
            await edit_msg.edit(content=sentence)

    @commands.command(aliases=["mkv",])
    async def markov(self, ctx, *, user: discord.Member = None):
        """A Markov chain is a model of some random process that happens over time. Markov chains are called that because they follow a rule called the Markov property. The Markov property says that whatever happens next in a process only depends on how it is right now (the state). It doesn't have a "memory" of how it was before. It is helpful to think of a Markov chain as evolving through discrete steps in time, although the "step" doesn't need to have anything to do with time. """
        source_data = ""
        edit_msg = await ctx.send("Thinking...")

        if user is None:
            async for msg in ctx.channel.history(limit=5000):
                if msg.content != "" and not msg.author.bot:
                    source_data += "\r\n" + str(msg.content).capitalize()
        else:
            if user.bot:
                embed = discord.Embed(title="You can't do that!", color=0xFF0000)
                embed.set_image(url="http://m.quickmeme.com/img/96/9651e121dac222fdac699ca6d962b84f288c75e6ec120f4a06e3c04f139ee8ec.jpg")
                await edit_msg.edit(content="", embed=embed)
                return

            async for msg in ctx.channel.history(limit=5000):
                if msg.content != "" and str(msg.author) == str(user) and not msg.author.bot:
                    source_data += "\r\n" + str(msg.content).capitalize()

        if not source_data:
            await edit_msg.edit(content="You broke me! _(Most likely the user hasn't commented in this channel.)_")
            return
        elif len(source_data) < 10:
            await edit_msg.edit(content="Not enough data! Good bye.")
            return

        chain = markovify.NewlineText(source_data, well_formed=True)
        sentence = chain.make_short_sentence(max_chars=300)

        if sentence is None:
            await edit_msg.edit(content="User [{}] does not have enough data. They suck!".format(user))
        else:
            await edit_msg.edit(content=sentence)

    @commands.command(aliases=["cd",])
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

        # def isDST():
        #     """ Compares January 1st of the current year to datetime.now() """
        #     x = datetime.datetime(datetime.datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone(timezone_cst))
        #     y = datetime.datetime.now(pytz.timezone(timezone_cst))
        #     val = int(not (y.utcoffset() == x.utcoffset()))
        #     print("isDST == {}".format(val))
        #     return val

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
            #gameDT -= datetime.timedelta(hours=isDST())

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
        else:
            for game in huskerSchedule:
                gameDT = datetime.datetime.strptime(game['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ")
                gameDT = pytz.utc.localize(gameDT)
                #gameDT -= datetime.timedelta(hours=isDST())

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

            dump = True
            if dump:
                with open("venue_dict.json", "w") as fp:
                    json.dump(venue_dict, fp, sort_keys=True, indent=4)
                fp.close()

            coords = {}
            for venues in venue_dict:
                if venues["name"] == venue:
                    coords = venues["location"]
        else:
            await ctx.send("Unable to locate venue.")
            return

        if which == "current":
            r = requests.get(url="https://api.weatherbit.io/v2.0/current?key={}&lang=en&units=I&lat={}&lon={}".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = True
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            embed = discord.Embed(
                title="Weather Forecast for __[{}]__ in __[{}, {}]__".format(venue, weather_dict["data"][0]["city_name"], weather_dict["data"][0]["state_code"]),
                color=0xFF0000,
                description="Nebraska's next opponent is __[{}]__".format(next_game))
            embed.set_thumbnail(url="https://www.weatherbit.io/static/img/icons/{}.png".format(weather_dict["data"][0]["weather"]["icon"]))
            embed.add_field(name="Temperature", value="{} F".format(weather_dict["data"][0]["temp"]))
            embed.add_field(name="Cloud Coverage", value="{}%".format(weather_dict["data"][0]["clouds"]))
            embed.add_field(name="Wind Speed", value="{} MPH / {}".format(weather_dict["data"][0]["wind_spd"], weather_dict["data"][0]["wind_cdir"]))
            embed.add_field(name="Snow Chance", value="{:.2f}%".format(weather_dict["data"][0]["snow"]*100))
            embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(weather_dict["data"][0]["precip"]*100))
        elif which == "forecast":
            r = requests.get(url="https://api.weatherbit.io/v2.0/forecast/daily?key={}&lang=en&units=I&lat={}&lon={}&days=7".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = True
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            embed = discord.Embed(
                title="Game day forecast for Nebraska's next game at {} in {}, {}".format(venue, weather_dict["city_name"], weather_dict["state_code"]),
                color=0xFF0000,
                description="Nebraska's next game is __[{}]__".format(next_game))
            for days in weather_dict["data"]:
                datetime_obj = datetime.datetime.strptime(days["datetime"], "%Y-%m-%d")
                if datetime_obj.weekday() == 5:
                    embed.set_thumbnail(url="https://www.weatherbit.io/static/img/icons/{}.png".format(days["weather"]["icon"]))
                    embed.add_field(name="Temperature", value="{} F".format(days["temp"]))
                    embed.add_field(name="Cloud Coverage", value="{}%".format(days["clouds"]))
                    embed.add_field(name="Wind Speed", value="{} MPH / {}".format(days["wind_spd"], days["wind_cdir"]))
                    embed.add_field(name="Snow Chance", value="{:.2f}%".format(days["snow"] * 100))
                    embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(days["precip"] * 100))
        else:
            await ctx.send("`Current` and `forecast` are the only options for `$weather`. Please try again.")
            return

        embed.set_footer(text="There is a daily 500 call limit to the API used for this command. Do not abuse it.")
        await ctx.send(embed=embed)

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