from discord.ext import commands
import mysql, config, random, discord, time

errors = {
    "wrong_channel": "You used the command in the wrong channel!",
    "already_setup": "There is already a game setup. To start a new game you must perform `$trivia quit` first.",
    "not_setup": "The game is not setup. To setup a game you must perform `$trivia setup` first.",
    "already_started": "The game is already started!"
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
        embed.add_field(name=field[0], value=field[1])
    return embed


async def loop_questions(chan: discord.TextChannel):
    if game.started:
        question_list = [
            game.questions[game.current_question]["correct"],
            game.questions[game.current_question]["wrong_1"],
            game.questions[game.current_question]["wrong_2"],
            game.questions[game.current_question]["wrong_3"]
        ]
        random.shuffle(question_list)
        question_msg = "1️⃣: {}\n" \
                       "2️⃣: {}\n" \
                       "3️⃣: {}\n" \
                       "4️⃣: {}".format(
            question_list[0],
            question_list[1],
            question_list[2],
            question_list[3]
        )

        question_embed = trivia_embed(
                [game.questions[game.current_question]["question"], question_msg]
            )
        msg = await chan.send(
            embed=question_embed
        )
        await add_reactions(msg)
        time.sleep(game.timer)
        question_embed.add_field(name="Status", value="🛑 Timed out! 🛑")
        await msg.edit(embed=question_embed)

        game.questions[game.current_question]["answered"] = True
        game.current_question += 1


class TriviaGame():
    def __init__(self, channel, question=None):
        self.channel = None
        self.current_question = 0
        self.questions = list()
        self.timer = int()
        self.setup_complete = False
        self.started = False

    def setup(self, chan: discord.TextChannel, timer=None):
        self.channel = chan
        if timer:
            self.timer = timer
        else:
            self.timer = 10
        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveTriviaQuestions)
            trivia_questions = cursor.fetchall()
        mysql.sqlConnection.commit()
        for question in trivia_questions:
            question["answered"] = False
        random.shuffle(trivia_questions)
        self.questions = trivia_questions
        self.setup_complete = True

    def correct_channel(self, chan):
        if chan == self.channel:
            return True
        else:
            return False


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
            pass

        timer = abs(timer)
        game.setup(chan, timer)
        await ctx.send(
            embed=trivia_embed(
                ["Channel", chan],
                ["Question Timer", timer],
                ["Number of Questions", len(game.questions)]
            )
        )

    @trivia.command()
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def start(self, ctx):
        """Admin/Trivia Boss Command: Starts the trivia game"""
        if not game.correct_channel(ctx.channel):
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["wrong_channel"]]
                )
            )
            return

        if game.setup_complete:
            game.started = True
            embed = trivia_embed(
                ["Rules", "You have {} seconds to answer by reacting to questions. Each question is worth 1,000 points per second and will count down to 0 after {} seconds.".format(game.timer, game.timer)],
                ["Game Status", "The game is starting soon! Get ready for the first question!"],
                ["Countdown...", game.timer]
            )
            msg = await game.channel.send(embed=embed)
            for index in range(game.timer, -1, -1):
                embed = trivia_embed(
                    ["Rules", "You have {} seconds to answer by reacting to questions. Each question is worth 1,000 points per second and will count down to 0 after {} seconds.".format(game.timer, game.timer)],
                    ["Game Status", "The game is starting soon! Get ready for the first question!"],
                    ["Countdown...", index]
                )
                await msg.edit(embed=embed)
                time.sleep(1)

            # countdown_message = await game.channel.send("```\nGet ready!\n```")
            # for index in range(game.timer, -1, -1):
            #     time.sleep(1)
            #     await countdown_message.edit(content="```\n{}...\n```".format(index))
            # await countdown_message.edit(content="```\nStarting!\n```")
            # time.sleep(1)
            # await countdown_message.delete()
        else:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["already_started"]]
                )
            )

        await loop_questions(game.channel)

    @trivia.command(aliases=["n",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def next(self, ctx):
        """Admin/Trivia Boss Command: Send the next question"""
        pass

    @trivia.command(aliases=["q",])
    @commands.has_any_role(606301197426753536, 440639061191950336)
    async def quit(self, ctx):
        """Admin/Trivia Boss Command: Quit the current trivia game"""
        game.started = False
        await ctx.send(
            embed=trivia_embed(
                ["Quitting", "The current trivia game has ended!"]
            )
        )

    @trivia.command(aliases=["score",])
    async def scores(self, ctx):
        """Shows the score for the current trivia game"""
        pass


def setup(bot):
    bot.add_cog(Trivia(bot))
