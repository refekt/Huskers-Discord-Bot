from discord.ext import commands
import discord
import markovify
import datetime
import random
import json
import datetime
from dateutil.parser import parse
import pandas as pd

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
bet_emojis = ["⬆", "⬇"]

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
    async def bet(self, ctx):
        """ Allows a user to bet on the outcome of the next game """
        f = open('husker_schedule.json', 'r')
        temp_json = f.read()
        husker_schedule = json.loads(temp_json)
        current_game = []
        for events in husker_schedule['schedule']['events']:
            # Find first game that is scheduled after now()
            check_date = datetime.datetime(year=int(events['dateYYYY']), month=int(events['dateMM']), day=int(events['dateDD']), hour=int(events['dateHH24']), minute=int(events['dateMI']))
            check_now = datetime.datetime.now()
            # print("Game [{}]\n{}\n{}".format(events['opponent'], check_date, check_now))

            if check_now < check_date:
                current_game.append(events['opponent'])
                current_game.append(check_date)
                break

        # print(current_game)
        msg_sent = await ctx.send("The next game on the schedule is: __{}__. Use ⬆ to bet for a win. Use ⬇ to bet for a loss.".format(current_game[0]))
        for e in bet_emojis:
            await msg_sent.add_reaction(e)

    # Text commands

def setup(bot):
    bot.add_cog(TextCommands(bot))