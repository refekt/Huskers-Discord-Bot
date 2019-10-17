from discord.ext import commands
from discord.ext.commands import TextChannelConverter
import mysql, config, random, discord, time, asyncio
from datetime import datetime

errors = {
    "wrong_channel": "You used the command in the wrong channel!",
    "already_setup": "There is already a game setup. To start a new game you must perform `$trivia quit` first.",
    "not_setup": "The game is not setup. To setup a game you must perform `$trivia setup` first.",
    "already_started": "The game is already started!",
    "trivia_master": "You are not the Trivia Master! Denied.",
    "unknown": "Unknown error!",
    "setup_error": "One or more inputs was incorrect. Try again!"
}

trivia_categories = ("all", "huskers")


async def add_reactions(message: discord.Message):
    reactions = ("💓", "💛", "💚", "💙", "⏭")
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


async def start_messagse():
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
    else:
        await game.channel.send(
            embed=trivia_embed(
                ["Error!", errors["already_started"]]
            )
        )
        return

    await loop_questions()


async def loop_questions():  # chan: discord.TextChannel):
    if game.started:
        game.processing = True

        question_list = [
            game.questions[game.current_question]["correct"],
            game.questions[game.current_question]["wrong_1"],
            game.questions[game.current_question]["wrong_2"],
            game.questions[game.current_question]["wrong_3"]
        ]

        random.shuffle(question_list)

        # reactions = ("💓", "💛", "💚", "💙")
        question_msg = "💓: {}\n💛: {}\n💚: {}\n💙: {}".format(
            question_list[0],
            question_list[1],
            question_list[2],
            question_list[3]
        )
        question_embed = trivia_embed(
                [game.questions[game.current_question]["question"], question_msg]
            )

        msg = await game.channel.send(
            embed=trivia_embed(["Question Loading...", "Answers Loading..."])
        )
        await add_reactions(msg)
        time.sleep(1)

        game.current_question_dt = datetime.now()
        question_embed.set_footer(text=str(game.current_question_dt))
        await msg.edit(embed=question_embed)

        await asyncio.sleep(game.timer + (config.bot_latency()/100))

        question_embed.add_field(name="Status", value="🛑 Timed out! 🛑")

        now = datetime.now()
        old = datetime.strptime(question_embed.footer.text, "%Y-%m-%d %H:%M:%S.%f")
        question_embed.set_footer(text="{}|{}".format(question_embed.footer.text,now,now-old))
        await msg.edit(embed=question_embed)

        game.current_question += 1
        game.add_to_collection(msg)
        game.processing = False

        def check_reaction(r, u):
            return u == game.trivia_master and str(r.emoji) == "⏭"

        if game.current_question >= len(game.questions):
            await quit_game()

        try:
            reaction, user = await config.client.wait_for("reaction_add", check=check_reaction)
        except asyncio.TimeoutError:
            pass
        else:
            if not game.processing and game.started:
                await loop_questions()


def scoreboard():
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlRetrieveTriviaScores)
    mysql.sqlConnection.commit()
    scores = cursor.fetchall()
    cursor.close()

    if scores:
        scores_edited = ""
        for score in scores:
            scores_edited += "{}: {}\n".format(score["user"], score["score"])
        return scores_edited
    else:
        return "N/A"


async def quit_game():
    global game
    await delete_collection()

    scores = scoreboard()

    await game.channel.send(
        embed=trivia_embed(
            ["Quitting", "The current trivia game has ended!"],
            ["Scores", scores]
        )
    )

    game = TriviaGame(channel=None)


async def delete_collection():
    await game.channel.delete_messages(game.message_collection)


def tally_score(message: discord.Message, author: discord.Member, end):
    """1000 points per second"""
    footer_text = message.embeds[0].footer.text
    start = datetime.strptime(footer_text.split("|")[0].strip(), "%Y-%m-%d %H:%M:%S.%f")
    diff = end - start
    score = diff.total_seconds()
    score *= 1000
    score = (game.timer * 1000) - score

    print("===\n= User: {}\n= Score: {}\n===\n".format(author.display_name, score))

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

    def setup(self, user: discord.Member, chan, timer, questions):
        self.trivia_master = user
        self.channel = chan
        self.timer = int(timer)

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveTriviaQuestions)
            trivia_questions = cursor.fetchall()
        mysql.sqlConnection.commit()
        cursor.close()
        random.shuffle(trivia_questions)

        self.questions = trivia_questions[0:int(questions)]
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
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def setup(self, ctx): #, chan: discord.TextChannel, timer=10, questions=15, category=None):
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

        game.trivia_master = ctx.message.author

        setup_questions = [
            ["Channel", "What channel do you want to use?"],
            ["Timer", "How long of a question timer do you want to use?"],
            ["Questions", "How many question do you want to use?"],
            ["Category", "What category do you want to use? (all, huskers, ...)"]
        ]

        def check_channel(m):
            if m.author == game.trivia_master and m.clean_content.split("#")[1] in [c.name for c in m.guild.channels]:
                return True
            else:
                return False

        def check_timer_and_questions(m):
            if m.author == game.trivia_master and m.content.isnumeric():
                return True
            else:
                return False

        def check_category(m):
            if m.author == game.trivia_master and m.content in trivia_categories:
                return True
            else:
                return False

        setup_chan = setup_timer = setup_question_length = setup_category = None

        chan_setup = True
        while chan_setup:
            sent_msg = await ctx.send(setup_questions[0][1])
            game.message_collection.append(sent_msg)

            try:
                print("Trying channel...")
                msg = await config.client.wait_for("message", check=check_channel)
                print("msg", msg.content)
                if msg:
                    print("setting up channel")
                    setup_chan = await TextChannelConverter().convert(ctx, msg.content)
                    print("chan", setup_chan.name)
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid Text Channel. Try again!")
                game.message_collection.append(sent_msg)
            else:
                print("chan_setup=false")
                chan_setup = False

        timer_setup = True
        while timer_setup:
            sent_msg = await ctx.send(setup_questions[1][1])
            game.message_collection.append(sent_msg)

            try:
                msg = await config.client.wait_for("message", check=check_timer_and_questions)
                if msg:
                    setup_timer = abs(int(msg.content))
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid question timer. Try again!")
                game.message_collection.append(sent_msg)
            else:
                timer_setup = False

        question_length_setup = True
        while question_length_setup:
            sent_msg = await ctx.send(setup_questions[2][1])
            game.message_collection.append(sent_msg)

            try:
                msg = await config.client.wait_for("message", check=check_timer_and_questions)
                if not msg == "N/A":
                    setup_question_length = abs(int(msg.content))
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid number of questions. Try again!")
                game.message_collection.append(sent_msg)
            else:
                question_length_setup = False

        #TODO Categories will goo here...

        game.setup(ctx.message.author, setup_chan, setup_timer, setup_question_length)

        msg = await ctx.send(
            embed=trivia_embed(
                ["Status", "Setup Completed! React 🆗 to start the game or use `$trivia start`."],
                ["Channel", game.channel.mention],
                ["Timer", game.timer],
                ["Number of Questions", len(game.questions)],
                ["Category", "TBD"]
            )
        )
        game.message_collection.append(msg)
        await msg.add_reaction("🆗")

        def check_reaction(r, u):
            return u == game.trivia_master and str(r.emoji) == "🆗"

        try:
            reaction, user = await config.client.wait_for("reaction_add", check=check_reaction)
        except asyncio.TimeoutError:
            await ctx.send("ur dumb lol")
        else:
            await start_messagse()

    # @setup.error
    # async def setup_handler(self, ctx, error):
    #     await ctx.send(
    #         embed=trivia_embed(
    #             ["Setup Error!", errors["setup_error"]]
    #         )
    #     )
    #     global game
    #     game = TriviaGame(channel=None)

    @trivia.command()
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def start(self, ctx):
        """Admin/Trivia Boss Command: Starts the trivia game"""
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )
            return

        await start_messagse()

    @trivia.command(aliases=["n",], hidden=True)
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def next(self, ctx):
        """Admin/Trivia Boss Command: Send the next question"""
        global game
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )
            return

        if not game.processing and game.started:
            await loop_questions()

    @trivia.command(aliases=["q",])
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def quit(self, ctx):
        """Admin/Trivia Boss Command: Quit the current trivia game"""
        await quit_game()

    @trivia.command(aliases=["score",], hidden=True)
    async def scores(self, ctx):
        """Shows the score for the current trivia game"""
        if not game.started:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["not_setup"]]
                )
            )
            return

        scores = scoreboard()
        await game.channel.send(
            embed=trivia_embed(
                ["Scoreboard", scores]
            )
        )


def setup(bot):
    bot.add_cog(Trivia(bot))
