from discord.ext import commands
import mysql, config, random, discord


def load_questions():
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlRetrieveTriviaQuestions)
        trivia_questions = cursor.fetchall()
    mysql.sqlConnection.commit()
    random.shuffle(trivia_questions)
    return random.choice(trivia_questions)


class TriviaGame():
    def __init__(self, channel, question=None):
        self.channel = channel
        self.question = question
        self.qtimer = 10

    def setup(self, chan: discord.TextChannel, timer: int):
        self.question = chan
        self.qtimer = timer


class Trivia(commands.Cog, name="Husker Trivia"):
    @commands.group()
    async def trivia(self, ctx):
        """Husker trivia"""
        pass

    @trivia.command(aliases=["s",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def setup(self, ctx, chan: discord.TextChannel, timer: int):
        """Admin/Trivia Boss Command: Setup the next trivia game"""
        game = TriviaGame(channel=chan)
        game.setup(chan, abs(timer))

    @setup.error
    async def setup_handler(self, ctx, error):
        pass

    @trivia.command()
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def start(self, ctx):
        """Admin/Trivia Boss Command: Starts the trivia game"""
        pass

    @trivia.command(aliases=["n",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def next(self, ctx):
        """Admin/Trivia Boss Command: Send the next question"""
        pass

    @trivia.command(aliases=["q",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def quit(self, ctx):
        """Admin/Trivia Boss Command: Quit the current trivia game"""
        pass

    @trivia.command(aliases=["score",])
    async def scores(self, ctx):
        """Shows the score for the current trivia game"""
        pass


def setup(bot):
    bot.add_cog(Trivia(bot))
