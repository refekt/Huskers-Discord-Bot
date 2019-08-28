from discord.ext import commands
import markovify
import random
import json
import datetime
import dateutil.parser
import discord
import config
import requests

# Dictionaries
eight_ball = ['Try again',
              'Definitely yes',
              'It is certain',
              'Ask again later',
              'Better not tell you now',
              'Cannot predict now',
              'Concentrate and ask again',
              'As I see it, yes',
              'Most Likely',
              'These are the affirmative answers.',
              'Don’t count on it',
              'My reply is no',
              'My sources say no',
              'Outlook not so good, and very doubtful',
              'Reply hazy',
              'Try again',
              'It is decidedly so',
              'Without a doubt',
              'Yes – definitely',
              'You may rely on it',
              'Fuck Iowa',
              'Frosty',
              'Scott Frost approves',
              'Coach V\'s cigar would like this'
               ]
bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]
husker_schedule = []
stored_bets = dict()


# Load season bets
def load_season_bets():
    f = open('season_bets.json', 'r')
    temp_json = f.read()
    config.season_bets = json.loads(temp_json)
    f.close()


# Allows the ability to load next opponent for sub commands.
def store_next_opponent():
    # Open previously generated JSON from $schedule.
    # To refresh change dump = True manually
    f = open('husker_schedule.json', 'r')
    temp_json = f.read()
    husker_schedule = json.loads(temp_json)
    f.close()

    # Find first game that is scheduled after now()
    counter = 1
    for events in husker_schedule:
        # The date/time is stored in ISO 8601 format. It sucks. Take raw data and manually convert it to the default format.
        check_date_raw = dateutil.parser.parse(events["start_date"])
        check_date = datetime.datetime(day=check_date_raw.day, month=check_date_raw.month, year=check_date_raw.year, hour=check_date_raw.hour, minute=check_date_raw.minute)
        check_date = check_date - datetime.timedelta(hours=5)

        check_now = datetime.datetime.now()
        #check_now = datetime.datetime(day=check_now_raw.day, month=check_now_raw.month, year=check_now_raw.year, hour=check_now_raw.hour, minute=check_now_raw.minute)

        if check_now < check_date:
            if events["home_team"] != "Nebraska":
                config.current_game.append(events["home_team"])
            else:
                config.current_game.append(events["away_team"])
            config.current_game.append(check_date)
            config.current_game.append(counter)
            break
        # Used for navigating season_bets JSON
        counter += 1


class TextCommands(commands.Cog, name="Text Commands"):
    # Text commands
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

            game_datetime_raw = husker_sched[game_index]['start_date'].split("T")
            game_datetime = datetime.datetime.strptime("{} {}".format(game_datetime_raw[0], game_datetime_raw[1][:-5]), "%Y-%m-%d %H:%M:%S")  # "%b %d, %Y %I:%M %p"
            game_datetime = datetime.datetime(year=game_datetime.year, month=game_datetime.month, day=game_datetime.day, hour=game_datetime.hour, minute=game_datetime.minute, second=game_datetime.second, tzinfo=game_datetime.tzinfo)

            days_left = game_datetime - datetime.datetime.now()
            cd_string = "📢📅 There are __[{} days, {} hours, and {} minutes]__ remaining until the __[{} vs. {}]__ game kicks off at __[{}]__ on __[{}/{}/{}]__".format(
                days_left.days,
                int(days_left.seconds / 3600),
                int((days_left.seconds / 60) % 60),
                husker_sched[game_index]['home_team'], husker_sched[game_index]['away_team'],
                datetime.time(hour=game_datetime.hour, minute=game_datetime.minute),
                game_datetime.month,
                game_datetime.day,
                game_datetime.year)
        else:
            for game in husker_sched:
                game_datetime_raw = game['start_date'].split("T")
                game_datetime = datetime.datetime.strptime("{} {}".format(game_datetime_raw[0], game_datetime_raw[1][:-5]), "%Y-%m-%d %H:%M:%S") # "%b %d, %Y %I:%M %p"
                game_datetime = datetime.datetime(year=game_datetime.year, month=game_datetime.month, day=game_datetime.day, hour=game_datetime.hour-5, minute=game_datetime.minute, second=game_datetime.second, tzinfo=game_datetime.tzinfo)

                if datetime.datetime.now() < game_datetime:
                    days_left = game_datetime - datetime.datetime.now()
                    cd_string = "📢📅 There are __[{} days, {} hours, and {} minutes]__ remaining until the __[{} vs. {}]__ game kicks off at __[{}]__ on __[{}/{}/{}]__".format(
                        days_left.days,
                        int(days_left.seconds/3600),
                        int((days_left.seconds/60)%60),
                        game['home_team'], game['away_team'],
                        datetime.time(hour=game_datetime.hour, minute=game_datetime.minute),
                        game_datetime.month,
                        game_datetime.day,
                        game_datetime.year)
                    break
                else:
                    cd_string = "Something went wrong 🤫!"

                counter += 1

        await ctx.send(cd_string)

    @commands.command(aliases=["bf", "facts",])
    async def billyfacts(self, ctx):
        """ Real facts about Bill Callahan. """
        facts = []
        with open("facts.txt") as f:
            for line in f:
                facts.append(line)
        f.close()

        random.shuffle(facts)
        await ctx.message.channel.send(random.choice(facts))

    @commands.command(aliases=["8b",])
    async def eightball(self, ctx, *, question):
        """ Ask a Magic 8-Ball a question. """
        random.shuffle(eight_ball)
        dice_roll = random.randint(0, len(eight_ball))

        embed = discord.Embed(title=':8ball: HuskerBot 8-Ball :8ball:')
        embed.add_field(name=question, value=eight_ball[dice_roll])

        await ctx.send(embed=embed)

    @commands.command()
    async def bet(self, ctx, cmd=None, *, team=None):
        """ Allows a user to place a bet on the upcoming Husker game. Bets are placed by reacting to the bot's message. Bets are recorded by Discord username. Changing your username will result in lost bets. All bets must be completed prior to kickoff. Bets after that will not be accepted. Winners will be tallied on the next calendar day after the game.
        There are 3 sub commands: all, show, and winners.

        Show: show your current bet.
        All: show all current bets.
        Winners <team>: show all the winners of a specific game.
        """
        # Creates the embed object for all messages within method
        embed = discord.Embed(title="Husker Game Betting", description="How do you think the Huskers will do in their next game? Place your bets below!", color=0xff0000)
        embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
        embed.set_footer(text=config.bet_footer)

        # Load next opponent and bets
        store_next_opponent()
        load_season_bets()

        game = config.current_game[0].lower()
        season_year = int(datetime.date.today().year) - 2019  # Future proof
        raw_username = "{}".format(ctx.author)

        # Outputs the betting message to allow the user to see the upcoming opponent and voting reactions.
        if cmd == None:
            if not team:
                team = config.current_game[0].lower()

            url = "https://api.collegefootballdata.com/lines?year={}&week={}&seasonType=regular&team=nebraska".format(config.current_game[1].year, config.current_game[2])
            game_date = []
            try:
                r = requests.get(url)
                game_data_raw = r.json()
            except:
                await ctx.send("An error occurred retrieving line data.")
                return

            lines = {}
            for lines_raw in game_data_raw:
                lines = lines_raw["lines"]
            lines = lines[0]

            embed.add_field(name="Opponent", value="{}\n{}".format(config.current_game[0], config.current_game[1].strftime("%B %d, %Y at %H:%M %p CST")), inline=False)
            embed.add_field(name="Rules", value="All bets must be made before kick off and only the most recent bet counts. You can only vote for a win or loss and cover or not covering spread. Bets are stored by your _Discord username_. If you change your username you will lose your bet history.\n", inline=False)
            embed.add_field(name="Spread ({})".format(lines["provider"]), value="{}".format(lines["spread"]), inline=False)
            embed.add_field(name="Over Under ({})".format(lines["provider"]), value="{}".format(lines["overUnder"]), inline=False)
            embed.add_field(name="Vote Instructions", value=""
                                                            "Bets winning (⬆) or losing (⬇) the game. Clear bet (❎).\n"
                                                            "Bets over (⏫) or under (⏬) on the spread. Clear bet (❌).\n"
                                                            "Bets over (🔼) or under (🔽) on total points. Clear bet (✖).\n", inline=False)

            # Store message sent in an object to allow for reactions afterwards
            msg_sent = await ctx.send(embed=embed)
            for e in bet_emojis:
                await msg_sent.add_reaction(e)

        # Show the user's current bet(s)
        elif cmd == "show":
            # Creates the embed object for all messages within method
            embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            embed.set_footer(text=config.bet_footer)

            temp_dict = config.season_bets[season_year]['opponent'][game]['bets'][0]
            for usr in temp_dict:
                if usr == raw_username:
                    winorlose = temp_dict[usr]['winorlose']
                    if winorlose == "True":
                        winorlose = "Win"
                    elif winorlose == "False":
                        winorlose = "Lose"
                    else:
                        winorlose = "N/A"

                    spread = temp_dict[usr]['spread']
                    if spread == "True":
                        spread = "Over"
                    elif spread == "False":
                        spread = "Under"
                    else:
                        spread = "N/A"

                    moneyline = temp_dict[usr]['moneyline']
                    if moneyline == "True":
                        moneyline = "Over"
                    elif moneyline == "False":
                        moneyline = "Under"
                    else:
                        moneyline = "N/A"

                    embed.add_field(name="Author", value=raw_username, inline=False)
                    embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
                    embed.add_field(name="Win or Loss", value=winorlose, inline=True)
                    embed.add_field(name="Spread", value=spread, inline=True)
                    embed.add_field(name="Moneyline", value=moneyline, inline=True)
                    await ctx.send(embed=embed)

        # Show all bets for the current game
        elif cmd == "all":
            # Creates the embed object for all messages within method
            embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            embed.set_footer(text=config.bet_footer)

            temp_dict = config.season_bets[season_year]['opponent'][game]['bets'][0]
            total_wins = 0
            total_losses = 0
            total_cover_spread = 0
            total_not_cover_spread = 0
            total_cover_moneyline = 0
            total_not_cover_moneyline = 0

            for usr in temp_dict:
                if temp_dict[usr]['winorlose'] == "True":
                    total_wins += 1
                else:
                    total_losses += 1

                if temp_dict[usr]['spread'] == "True":
                    total_cover_spread += 1
                else:
                    total_not_cover_spread += 1

                if temp_dict[usr]['moneyline'] == "True":
                    total_cover_moneyline += 1
                else:
                    total_not_cover_moneyline += 1

            total_winorlose = total_losses + total_wins
            total_spread = total_cover_spread + total_not_cover_spread
            total_moneyline = total_cover_moneyline + total_not_cover_moneyline

            embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
            embed.add_field(name="Wins", value="{} ({:.2f}%)".format(total_wins, (total_wins/total_winorlose) * 100))
            embed.add_field(name="Losses", value="{} ({:.2f}%)".format(total_losses, (total_losses / total_winorlose) * 100))

            embed.add_field(name="Cover Spread", value="{} ({:.2f}%)".format(total_cover_spread, (total_cover_spread / total_spread) * 100))
            embed.add_field(name="Not Cover Spread", value="{} ({:.2f}%)".format(total_not_cover_spread, (total_not_cover_spread / total_spread) * 100))

            embed.add_field(name="Cover Moneyline", value="{} ({:.2f}%)".format(total_cover_moneyline, (total_cover_moneyline / total_moneyline) * 100))
            embed.add_field(name="Not Cover Moneyline", value="{} ({:.2f}%)".format(total_not_cover_moneyline, (total_not_cover_moneyline / total_moneyline) * 100))
            await ctx.send(embed=embed)

        # Show all winners for game
        elif cmd == "winners":
            # Need to add check if command is run the day after the game
            if team:
                winners_winorlose = []
                winners_spread = []
                winners_moneyline = []

                try:
                    # Creates the embed object for all messages within method
                    embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
                    embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
                    embed.set_footer(text=config.bet_footer)

                    temp_dict = config.season_bets[season_year]['opponent'][team.lower()]['bets'][0]

                    outcome_winorlose = True
                    outcome_spread = True
                    outcome_moneyline = True

                    if config.season_bets[season_year]['opponent'][team.lower()]['outcome_winorlose'] == "None":
                        outcome_winorlose = False

                    if config.season_bets[season_year]['opponent'][team.lower()]['outcome_spread'] == "None":
                        outcome_spread = False

                    if config.season_bets[season_year]['opponent'][team.lower()]['outcome_moneyline'] == "None":
                        outcome_moneyline = False

                    for usr in temp_dict:
                        if temp_dict[usr]['winorlose'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_winorlose'] and outcome_winorlose:
                            winners_winorlose.append(usr)

                        if temp_dict[usr]['spread'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_spread'] and outcome_spread:
                            winners_spread.append(usr)

                        if temp_dict[usr]['moneyline'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_moneyline'] and outcome_moneyline:
                            winners_moneyline.append(usr)

                    win_winorlose_string = ""
                    win_spread_string = ""
                    win_moneyline_string = ""

                    if winners_winorlose:
                        for winner in winners_winorlose:
                            win_winorlose_string = win_winorlose_string + "{}\n".format(winner)

                    if winners_spread:
                        for winner in winners_spread:
                            win_spread_string = win_spread_string + "{}\n".format(winner)

                    if winners_moneyline:
                        for winner in winners_moneyline:
                            win_moneyline_string = win_moneyline_string + "{}\n".format(winner)

                    embed.add_field(name="Opponent", value=team.title(), inline=False)

                    if win_winorlose_string:
                        embed.add_field(name="Win/Loss Winners", value=win_winorlose_string, inline=True)
                    else:
                        embed.add_field(name="Win/Loss Winners", value="N/A", inline=True)

                    if win_spread_string:
                        embed.add_field(name="Spread Winners", value=win_spread_string, inline=True)
                    else:
                        embed.add_field(name="Spread Winners", value="N/A", inline=True)

                    if win_moneyline_string:
                        embed.add_field(name="Spread Winners", value=win_moneyline_string, inline=True)
                    else:
                        embed.add_field(name="Spread Winners", value="N/A", inline=True)

                    await ctx.send(embed=embed)

                except discord.HTTPException as err:
                    print("Embed Name: {}\nEmbed Value: {}".format(embed.fields[1].name, embed.fields[1].value))
                    print("Error Text: {}".format(err.text))
                    await ctx.send("Something happened in the backend of hte program. Please alert the bot owners!")
                except:
                    await ctx.send("Cannot find the opponent \"{}\". Please verify the team is on the schedule for the {} season and it is spelled correctly. Opponents can be found by using `$schedule|shed {}`".format(team, 2019+season_year, 2019+season_year))
            else:
                await ctx.send("An opponent team must be included. Example: `$bet winners South Alabama` or `$bet winners Iowa`")
            pass

        else:
            embed.add_field(name="Error", value="Unknown command. Please reference `$help bet`.")
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
                if venues["name"] == venue and venues["state"] == "NE":
                    coords = venues["location"]
        else:
            await ctx.send("Unable to locate venue.")
            return

        if which == "current":
            r = requests.get(url="https://api.weatherbit.io/v2.0/current?key={}&lang=en&units=I&lat={}&lon={}".format("39b7915267f04d5f88fa5fe6be6290e6", coords["x"], coords["y"]))
            weather_dict = r.json()

            dump = False
            if dump:
                with open("weather_json.json", "w") as fp:
                    json.dump(weather_dict, fp, sort_keys=True, indent=4)
                fp.close()

            embed = discord.Embed(
                title="Current weather forecast for Nebraska's next game at {} in {}, {}".format(venue, weather_dict["data"][0]["city_name"], weather_dict["data"][0]["state_code"]),
                color=0xFF0000,
                description="Nebraska's next game is __[{}]__".format(next_game))

            embed.add_field(name="Cloud Coverage", value="{}%".format(weather_dict["data"][0]["clouds"]))
            embed.add_field(name="Wind Speed", value="{} MPH / {}".format(weather_dict["data"][0]["wind_spd"], weather_dict["data"][0]["wind_cdir"]))
            embed.add_field(name="Snow Chance", value="{:.2f}%".format(weather_dict["data"][0]["snow"]*100))
            embed.add_field(name="Precipitation Chance", value="{:.2f}%".format(weather_dict["data"][0]["precip"]*100))
            embed.add_field(name="Temperature", value="{} F".format(weather_dict["data"][0]["temp"]))
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

            for days in weather_dict["data"]:
                day_str = "Cloud Coverage: {}%\n" \
                          "Wind: {} MPH {}\n" \
                          "Snow Chance: {:.2f}%\n" \
                          "Precip Chance: {:.2f}%\n" \
                          "High Temp: {} F\n" \
                          "Low Temp: {} F\n".format(days["clouds"], days["wind_spd"], days["wind_cdir"], days["snow"]*100, days["precip"]*100, days["max_temp"], days["min_temp"])
                embed.add_field(name="{}".format(days["datetime"]), value=day_str)
        else:
            await ctx.send("`Current` and `forecast` are the only options for `$weather`. Please try again.")
            return

        embed.set_footer(text="There is a 500 call limit to the API used for this command. Do not abuse it.")
        await ctx.send(embed=embed)

        #await ctx.send(ow.get_weather(station))
    # Text commands


def setup(bot):
    bot.add_cog(TextCommands(bot))