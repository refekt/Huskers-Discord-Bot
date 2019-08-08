from discord.ext import commands
import markovify
import random
import json
import datetime
import discord
import config
import urllib3


# Dictionaries
eight_ball = ['Try again',
              'Definitely yes',
              'It is certain',
              'It is decidedly so',
              'Without a doubt',
              'Yes – definitely',
              'You may rely on it',
              'As I see it, yes',
              'Most Likely',
              'These are the affirmative answers.',
              'Don’t count on it',
              'My reply is no',
              'My sources say no',
              'Outlook not so good, and very doubtful',
              'Reply hazy',
              'Try again',
              'Ask again later',
              'Better not tell you now',
              'Cannot predict now',
              'Concentrate and ask again',
              'Fuck Iowa',
              'Scott Frost approves',
              'Coach V\'s cigar would like this'
               ]
husker_schedule = []
stored_bets = dict()


# Load season bets
def load_season_bets():
    f = open('season_bets.json', 'r')
    temp_json = f.read()
    config.season_bets = json.loads(temp_json)


# Allows the ability to load next opponent for sub commands.
def store_next_opponent():
    # Open previously generated JSON from $schedule.
    # To refresh change dump = True manually
    f = open('husker_schedule.json', 'r')
    temp_json = f.read()
    husker_schedule = json.loads(temp_json)

    counter = 0
    for events in husker_schedule['schedule']['events']:
        # Find first game that is scheduled after now()
        check_date = datetime.datetime(year=int(events['dateYYYY']), month=int(events['dateMM']), day=int(events['dateDD']), hour=int(events['dateHH24']), minute=int(events['dateMI']))
        check_now = datetime.datetime.now()

        if check_now < check_date:
            config.current_game.append(events['opponent'])
            config.current_game.append(check_date)
            config.current_game.append(counter - 1)
            break
        # Used for navigating season_bets JSON
        counter += 1


class TextCommands(commands.Cog, name="Text Commands"):
    # Text commands
    @commands.command()
    async def stonk(self, ctx):
        """ Isms hates stocks. """
        await ctx.send("Stonk!")

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
    async def countdown(self, ctx):
        season_start = datetime.datetime(year=2019, month=8, day=31,hour=12,minute=00)

        if season_start > datetime.datetime.now():
            days_left = season_start - datetime.datetime.now()
            await ctx.send("📢 There are {} days, {} hours, and {} minutes remaining until the Husker 2019 season kicks off!".format(days_left.days, int(days_left.seconds/3600),int((days_left.seconds/60)%60),days_left.seconds))
        else:
            await ctx.send("The season has already started dummy!")

    @commands.command()
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
            ###
            # https://mybookie.ag/sportsbook/college-football/nebraska/
            # This site could be used to pull spread information.
            ###

            embed.add_field(name="Opponent", value="{}\n{}".format(config.current_game[0], config.current_game[1].strftime("%B %d, %Y at %H:%M CST")), inline=False)
            embed.add_field(name="Rules", value="All bets must be made before kick off and only the most recent bet counts. You can only vote for a win or loss and cover or not covering spread. Bets are stored by your _Discord username_. If you change your username you will lose your bet history.\n", inline=False)
            embed.add_field(name="Spread", value="[Betting on the spread is a work in progress and may come later in the season. Sorry!]", inline=False)
            embed.add_field(name="Vote", value="⬆: Submits a bet that we will win the game.\n"
                                               "⬇: Submits a bet that we will lose the game.\n"
                                               "~~⏫: Submits a bet that we will beast the spread.~~\n"
                                               "~~⏬: Submits a bet that we will lose the spread.~~", inline=False)

            # Store message sent in an object to allow for reactions afterwards
            msg_sent = await ctx.send(embed=embed)
            for e in config.bet_emojis:
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
                    embed.add_field(name="Author", value=raw_username, inline=False)
                    embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
                    embed.add_field(name="Win or Loss", value=temp_dict[usr]['winorlose'], inline=True)
                    embed.add_field(name="Spread", value=temp_dict[usr]['spread'], inline=True)
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
            total_cover = 0
            total_not_cover = 0

            for usr in temp_dict:
                if temp_dict[usr]['winorlose']:
                    total_wins += 1
                else:
                    total_losses += 1
                if temp_dict[usr]['spread']:
                    total_cover += 1
                else:
                    total_not_cover += 1

            total_winorlose = total_losses + total_wins
            total_spread = total_cover + total_not_cover

            embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
            embed.add_field(name="Wins", value="{} ({:.2f}%)".format(total_wins, (total_wins/total_winorlose) * 100))
            embed.add_field(name="Losses", value="{} ({:.2f}%)".format(total_losses, (total_losses / total_winorlose) * 100))
            embed.add_field(name="Cover Spread", value="{} ({:.2f}%)".format(total_cover, (total_cover / total_spread) * 100))
            embed.add_field(name="Not Cover Spread", value="{} ({:.2f}%)".format(total_not_cover, (total_not_cover / total_spread) * 100))
            await ctx.send(embed=embed)

        # Show all winners for game
        elif cmd == "winners":
            # Need to add check if command is run the day after the game
            if team:
                winners_winorlose = []
                winners_spread = []
                try:
                    # Creates the embed object for all messages within method
                    embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
                    embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
                    embed.set_footer(text=config.bet_footer)

                    temp_dict = config.season_bets[season_year]['opponent'][team.lower()]['bets'][0]

                    for usr in temp_dict:
                        if temp_dict[usr]['winorlose'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_winorlose']:
                            winners_winorlose.append(usr)
                        if temp_dict[usr]['spread'] == config.season_bets[season_year]['opponent'][team.lower()]['outcome_spread']:
                            winners_spread.append(usr)

                    win_winorlose_string = ""
                    win_spread_string = ""

                    if winners_winorlose:
                        for winner in winners_winorlose:
                            win_winorlose_string = win_winorlose_string + "{}\n".format(winner)

                    if winners_spread:
                        for winner in winners_spread:
                            win_spread_string = win_spread_string + "{}\n".format(winner)

                    embed.add_field(name="Opponent", value=team.title(), inline=False)
                    if win_winorlose_string:
                        embed.add_field(name="Win/Loss Winners", value=win_winorlose_string, inline=True)
                    else:
                        embed.add_field(name="Win/Loss Winners", value="N/A", inline=True)
                    if win_spread_string:
                        embed.add_field(name="Spread Winners", value=win_spread_string, inline=True)
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
    # Text commands


def setup(bot):
    bot.add_cog(TextCommands(bot))