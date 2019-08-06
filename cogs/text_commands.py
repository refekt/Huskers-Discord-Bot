from discord.ext import commands
import discord
import markovify
import random
import json
import datetime
import discord
import config


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
        dice_roll = random.randint(0, len(eight_ball))

        embed = discord.Embed(title=':8ball: HuskerBot 8-Ball :8ball:')
        embed.add_field(name=question, value=eight_ball[dice_roll])

        await ctx.send(embed=embed)

    @commands.command()
    async def bet(self, ctx, cmd=None):
        """ Allows a user to bet on the outcome of the next game.
         Commands include: show. """
        # Creates the embed object for all messages within method
        embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
        embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
        embed.set_footer(text=config.bet_footer)

        # Outputs the betting message to allow the user to see the upcoming opponent and voting reactions.
        if cmd == None:
            # Load next opponent
            store_next_opponent()

            ###
            # https://mybookie.ag/sportsbook/college-football/nebraska/
            # This site could be used to pull spread information.
            ###

            embed.add_field(name="Opponent", value="{}\n{}".format(config.current_game[0], config.current_game[1].strftime("%B %d, %Y at %H:%M CST")), inline=False)
            embed.add_field(name="Rules", value="All bets must be made before kick off and only the most recent bet counts. You can only vote for a win or loss and cover or not covering spread.\n", inline=False)
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
            # Load next opponent and bets
            store_next_opponent()
            load_season_bets()

            game = config.current_game[2]

            for users in config.season_bets['game_details'][game]['bets']:
                if users['user'] == str(ctx.message.author):
                    stored_bets['user'] = users['user']
                    stored_bets['winorlose'] = users['winorlose']
                    stored_bets['spread'] = users['spread']
                    stored_bets['datetime'] = users['datetime']

            winorloss = ""
            spread = ""

            if stored_bets['winorlose'] != "":
                if stored_bets['winorlose']:
                    winorloss = config.bet_descriptions[0]
                else:
                    winorloss = config.bet_descriptions[1]

            if stored_bets['spread'] != "":
                if stored_bets['spread']:
                    spread = config.bet_descriptions[2]
                else:
                    spread = config.bet_descriptions[3]

            embed.add_field(name="User", value=str(ctx.message.author), inline=False)
            embed.add_field(name="Opponent", value=str(config.season_bets['game_details'][game]['game']), inline=False)
            if winorloss:
                embed.add_field(name="Win/Loss", value=winorloss, inline=False)
            if spread:
                embed.add_field(name="~~Spread~~", value="~~{}~~".format(spread), inline=False)
            await ctx.send(embed=embed)

        else:
            embed.add_field(name="Error", value="Unknown command. Please reference `$help bet`.")
            await ctx.send(embed=embed)
    # Text commands


def setup(bot):
    bot.add_cog(TextCommands(bot))