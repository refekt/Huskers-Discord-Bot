from discord.ext import commands
import mysql, config, random, discord, time
from datetime import datetime

errors = {
    "wrong_channel": "You used the command in the wrong channel!",
    "already_setup": "There is already a game setup. To start a new game you must perform `$trivia quit` first.",
    "not_setup": "The game is not setup. To setup a game you must perform `$trivia setup` first.",
    "already_started": "The game is already started!",
    "trivia_master": "You are not the Trivia Master! Denied.",
    "unknown": "Unknown error!"
}


async def add_reactions(message: discord.Message):
    reactions = ('1⃣', '2⃣', '3⃣', '4⃣')
    for reaction in reactions:
        await message.add_reaction(reaction)


def trivia_embed(*fields):
    embed = discord.Embed(title="Husker Discord Trivia", description="The Huskers Discord weekly trivia game!", color=0xFF0000)
    embed.set_footer(text="Frost Bot")
    embed.set_thumbnail(url="https://i.imgur.com/0Co9fOy.jpg")
    embed.set_author(name="Bot Frost", url="https://reddit.com/u/Bot_Frost", icon_url="https://i.imgur.com/Ah3x5NA.png")
    for field in fields:
        embed.add_field(name=field[0], value=field[1], inline=False)
    return embed


async def loop_questions(chan: discord.TextChannel):
    if game.started:
        game.processing = True

        question_list = [
            game.questions[game.current_question]["correct"],
            game.questions[game.current_question]["wrong_1"],
            game.questions[game.current_question]["wrong_2"],
            game.questions[game.current_question]["wrong_3"]
        ]
        random.shuffle(question_list)

        question_msg = "1️⃣: {}\n2️⃣: {}\n3️⃣: {}\n4️⃣: {}".format(
            question_list[0],
            question_list[1],
            question_list[2],
            question_list[3]
        )
        question_embed = trivia_embed(
                [game.questions[game.current_question]["question"], question_msg]
            )

        msg = await chan.send(
            embed=trivia_embed(["Question Loading...", "Answers Loading..."])
        )
        await add_reactions(msg)
        time.sleep(1)

        game.current_question_dt = datetime.now()
        question_embed.set_footer(text=str(game.current_question_dt))
        await msg.edit(embed=question_embed)

        time.sleep(game.timer)
        question_embed.add_field(name="Status", value="🛑 Timed out! 🛑")

        now = datetime.now()
        old = datetime.strptime(question_embed.footer.text, "%Y-%m-%d %H:%M:%S.%f")
        question_embed.set_footer(text="{}|{}".format(question_embed.footer.text,now,now-old))
        await msg.edit(embed=question_embed)

        game.current_question += 1
        game.add_to_collection(msg)
        game.processing = False

        if game.current_question > len(game.questions):
            await chan.send("The game is over!")


async def delete_collection():
    await game.channel.delete_messages(game.message_collection)


def tally_score(message: discord.Message, author: discord.Member, end):
    """1000 points per second"""
    footer_text = message.embeds[0].footer.text
    start = datetime.strptime(footer_text.split("|")[0].strip(), "%Y-%m-%d %H:%M:%S.%f")
    # end = datetime.strptime(footer_text.split("|")[1].strip(), "%Y-%m-%d %H:%M:%S.%f")
    diff = end - start
    score = (diff.total_seconds() - game.timer) * 1000
    print("score", score)

    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlInsertTriviaScore, (author.display_name, score, score))
    mysql.sqlConnection.commit()
    cursor.close()


class TriviaGame():
    def __init__(self, channel, question=None):
        self.channel = None
        self.current_question = 0
        self.current_question_dt = None
        self.questions = list()
        self.timer = int()
        self.setup_complete = False
        self.started = False
        self.processing = False
        self.trivia_master = None
        self.message_collection = list()

    def setup(self, user: discord.Member, chan: discord.TextChannel, timer=None):
        self.trivia_master = user
        self.channel = chan
        if timer:
            self.timer = timer
        else:
            self.timer = 10
        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveTriviaQuestions)
            trivia_questions = cursor.fetchall()
        mysql.sqlConnection.commit()
        cursor.close()
        random.shuffle(trivia_questions)
        self.questions = trivia_questions
        self.setup_complete = True

    def correct_channel(self, chan):
        if chan == self.channel:
            return True
        else:
            return False

    def add_to_collection(self, message: discord.Message):
        self.message_collection.append(message)


game = TriviaGame(channel=None)


class Trivia(commands.Cog, name="Husker Trivia"):
    @commands.group()
    async def trivia(self, ctx):
        """Husker trivia"""
        pass

    @trivia.command(aliases=["s",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def setup(self, ctx, chan: discord.TextChannel, timer=10):
        """Admin/Trivia Boss Command: Setup the next trivia game"""
        try:
            if game.setup_complete:
                await ctx.send(
                    embed=trivia_embed(
                        ["Error!", errors["already_setup"]]
                    )
                )
                return
        except:
            pass  # I don't know if the try/excpet is needed

        timer = abs(timer)
        game.setup(ctx.message.author, chan, timer)
        msg = await ctx.send(
            embed=trivia_embed(
                ["Channel", chan],
                ["Question Timer", timer],
                ["Number of Questions", len(game.questions)]
            )
        )
        game.add_to_collection(msg)

    @setup.error
    async def setup_handler(self, ctx, error):
        await ctx.send(errors["unknown"])

    @trivia.command()
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def start(self, ctx):
        """Admin/Trivia Boss Command: Starts the trivia game"""
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )

        if game.setup_complete:
            game.started = True
            embed = trivia_embed(
                ["Rules", "You have {} seconds to answer by reacting to questions. Each question is worth 1,000 points per second and will count down to 0 after {} seconds.".format(game.timer, game.timer)],
                ["Game Status", "The game is starting soon! Get ready for the first question!"],
                ["Countdown...", game.timer]
            )
            msg = await game.channel.send(embed=embed)
            for index in range(game.timer, -1, -1):
                embed.remove_field(2)
                embed.add_field(name="Countdown..", value=str(index))
                await msg.edit(embed=embed)
                time.sleep(1)
            await msg.delete()
        else:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["already_started"]]
                )
            )

        await loop_questions(game.channel)

    @start.error
    async def start_handler(self, ctx, error):
        await ctx.send(errors["unknown"])

    @trivia.command(aliases=["n",], hidden=True)
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def next(self, ctx):
        """Admin/Trivia Boss Command: Send the next question"""
        global game
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )

        if not game.processing:
            await loop_questions(game.channel)

    @next.error
    async def next_handler(self, ctx, error):
        await ctx.send(errors["unknown"])

    @trivia.command(aliases=["q",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def quit(self, ctx):
        """Admin/Trivia Boss Command: Quit the current trivia game"""
        global game
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )
        await delete_collection()
        game = TriviaGame(channel=None)
        await ctx.send(
            embed=trivia_embed(
                ["Quitting", "The current trivia game has ended!"]
            )
        )

    @quit.error
    async def quit_handler(self, ctx, error):
        await ctx.send(errors["unknown"])

    @trivia.command(aliases=["score",], hidden=True)
    async def scores(self, ctx):
        """Shows the score for the current trivia game"""
        pass


def setup(bot):
    bot.add_cog(Trivia(bot))
