import asyncio
import html
import random
import time
from datetime import datetime

import discord
import requests
from discord.ext import commands
from discord.ext.commands import TextChannelConverter

from utils.client import client
from utils.consts import ROLE_ADMIN_TEST, ROLE_ADMIN_PROD, ROLE_MOD_PROD
from utils.embed import build_embed
from utils.misc import bot_latency
from utils.mysql import process_MySQL, sqlClearTriviaScore, sqlRetrieveTriviaScores, sqlInsertTriviaScore, sqlRetrieveTriviaQuestions

errors = {
    "wrong_channel": "You used the command in the wrong channel!",
    "already_setup": "There is already a game setup. To start a new game you must perform `$trivia quit` first.",
    "not_setup": "The game is not setup. To setup a game you must perform `$trivia setup` first.",
    "already_started": "The game is already started!",
    "trivia_master": "You are not the Trivia Master! Denied.",
    "unknown": "Unknown error!",
    "setup_error": "One or more inputs was incorrect. Try again!"
}

trivia_cats = {
    "huskers": [0, "huskers"],
    "any": ["", "Any Category"],
    "animals": [27, "Animals"],
    "anime": [31, "Anime"],
    "art": [25, "Art"],
    "books": [10, "Books"],
    "cartoons": [32, "Cartoons"],
    "celebs": [26, "Celebs"],
    "computers": [18, "Computers"],
    "film": [11, "Film"],
    "gadgets": [30, "Gadgets"],
    "games": [15, "Video Games"],
    "general": [9, "General"],
    "geography": [22, "Geography"],
    "history": [23, "History"],
    "math": [19, "Math"],
    "music": [12, "Music"],
    "mythology": [20, "Mythology"],
    "politics": [24, "Politics"],
    "science": [17, "Science"],
    "sports": [21, "Sports"],
    "tv": [14, "Television"],
    "vehicles": [28, "Vehicles"]
}

# reactions = ("💓", "💛", "💚", "💙", "⏭")
reactions = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "⏭")


async def add_reactions(message: discord.Message):
    global reactions
    for reaction in reactions:
        await message.add_reaction(reaction)


def trivia_embed(*fields):
    return build_embed(
        title="Husker Discord Trivia",
        description="The Husker Discord trivia game!",
        thumbnail="https://i.imgur.com/0Co9fOy.jpg",
        fields=fields,
        inline=False
    )


def clear_scoreboard():
    process_MySQL(sqlClearTriviaScore)


async def start_messages():
    if game.setup_complete:
        game.started = True

        clear_scoreboard()

        embed = trivia_embed(
            ["Rules", f'You have __[{game.timer}]__ seconds to answer the question by reacting to the message. Each question is worth 1,000 points per second and will countdown to 0 points after '
                      f'__[{game.timer}]__ seconds.'],
            ["Game Status", "The game is starting soon! Get ready for the first question!"],
            ["Countdown...", game.timer]
        )

        msg = await game.channel.send(embed=embed)
        game.message_collection.append(msg)

        for index in range(10, -1, -1):
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


async def loop_questions():
    if game.started:
        game.processing = True

        msg = await game.channel.send(
            embed=trivia_embed(["Question Loading...", "Answers Loading..."])
        )
        await add_reactions(msg)
        time.sleep(1)

        question_list = [
            game.questions[game.current_question]["correct"],
            game.questions[game.current_question]["wrong_1"],
            game.questions[game.current_question]["wrong_2"],
            game.questions[game.current_question]["wrong_3"]
        ]
        random.shuffle(question_list)

        question_msg = f"{reactions[0]}: {question_list[0]}\n" \
                       f"{reactions[1]}: {question_list[1]}\n" \
                       f"{reactions[2]}: {question_list[2]}\n" \
                       f"{reactions[3]}: {question_list[3]}"

        question_embed = trivia_embed(
            ["Question Number", f'{game.current_question + 1} out of {len(game.questions)}'],
            [game.questions[game.current_question]["question"], question_msg]
        )

        game.current_question_dt = datetime.now()
        question_embed.set_footer(text=str(game.current_question_dt))

        await msg.edit(embed=question_embed)

        await asyncio.sleep(game.timer + bot_latency())

        question_embed.add_field(name="Correct Answer", inline=False, value=game.questions[game.current_question]["correct"])
        question_embed.add_field(name="Status", inline=False, value="🛑 Timed out! 🛑")

        now = datetime.now()
        old = datetime.strptime(question_embed.footer.text, "%Y-%m-%d %H:%M:%S.%f")
        question_embed.set_footer(text=f'{question_embed.footer.text}|{now} == {now-old}')
        await msg.edit(embed=question_embed)

        game.current_question += 1
        game.add_to_collection(msg)
        game.processing = False

        def check_reaction(r, u):
            return u == game.trivia_master and str(r.emoji) == "⏭"

        if game.current_question >= len(game.questions):
            await quit_game()

        try:
            reaction, user = await client.wait_for("reaction_add", check=check_reaction)
        except asyncio.TimeoutError:
            pass
        else:
            if not game.processing and game.started:
                await loop_questions()


def scoreboard():
    scores = process_MySQL(fetch="all", query=sqlRetrieveTriviaScores)

    if scores:
        scores_edited = ""
        for index, score in enumerate(scores):
            scores_edited += f'#{index + 1}. {score["user"]}: {score["score"]}\n'
        return scores_edited
    else:
        return "N/A"


async def quit_game():
    global game

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
    if end == 0:
        process_MySQL(query=sqlInsertTriviaScore, value=(author.display_name, 0, 0))
        print(f">>> {author} got a score of 0.")
        return

    footer_text = message.embeds[0].footer.text
    start = datetime.strptime(footer_text.split("|")[0].strip(), "%Y-%m-%d %H:%M:%S.%f")
    diff = end - start
    score = diff.total_seconds()
    score *= 1000
    score = (game.timer * 1000) - score
    print(f">>> {author} got a score of {score}.")

    process_MySQL(query=sqlInsertTriviaScore, values=(author.display_name, abs(score), abs(score)))


class TriviaGame:
    def __init__(self, channel, question=None):
        self.category_index = None
        self.category = None
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

    def setup(self, user: discord.Member, chan, timer, questions, category):
        self.trivia_master = user
        self.channel = chan
        self.timer = int(timer)

        if category[0] == 0:
            trivia_questions = process_MySQL(fetch="all", query=sqlRetrieveTriviaQuestions)
            random.shuffle(trivia_questions)
            self.questions = trivia_questions[0:int(questions)]
            self.category_index = category[0]
            self.category = category[1].title()
        else:
            self.category_index = category[0]
            self.category = category[1].title()

            url = f"https://opentdb.com/api.php?amount={questions}&category={self.category_index}&&type=multiple"
            q = []

            try:
                r = requests.get(url)
                for index, question in enumerate(r.json()["results"]):
                    q.append(
                        {
                            "question": html.unescape(question["question"]).strip("\r").strip("\n"),
                            "correct": html.unescape(question["correct_answer"]).strip("\r").strip("\n"),
                            "wrong_1": html.unescape(question["incorrect_answers"][0]).strip("\r").strip("\n"),
                            "wrong_2": html.unescape(question["incorrect_answers"][1]).strip("\r").strip("\n"),
                            "wrong_3": html.unescape(question["incorrect_answers"][2]).strip("\r").strip("\n")
                        }
                    )
            except:
                print("Error in questions....")
                return
            self.questions = q[0:int(questions)]

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
        if not ctx.invoked_subcommand:
            raise discord.ext.commands.CommandError(f"Missing a subcommand. Review '{client.command_prefix}help {ctx.command.qualified_name}' to view subcommands.")
        pass

    @trivia.command(aliases=["s",])
    # @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    async def setup(self, ctx):
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

        cat_list = ""
        for index, cat in enumerate(trivia_cats):
            pass
            cat_list += f"#{index + 1:2}: {cat}\n"

        setup_questions = [
            ["Channel", "What channel do you want to use?"],
            ["Timer", "How long of a question timer do you want to use?"],
            ["Questions", "How many question do you want to use?"],
            ["Category", f"What category do you want to use? Must match __exactly__ as:\n{cat_list}"]
        ]

        def check_channel(m):
            if "#" in m.clean_content:
                if m.author == game.trivia_master and m.clean_content.split("#")[1] in [c.name for c in m.guild.channels]:
                    return True
                else:
                    return False
            else:
                if m.author == game.trivia_master and m.clean_content in [c.name for c in m.guild.channels]:
                    return True
                else:
                    return False

        def check_timer_and_questions(m):
            if m.author == game.trivia_master and m.content.isnumeric():
                return True
            else:
                return False

        def check_category(m):
            if m.author == game.trivia_master and m.clean_content in [c for c in trivia_cats]:
                return True
            else:
                return False

        setup_chan = setup_timer = setup_question_length = setup_category = None

        chan_setup = True
        while chan_setup:
            sent_msg = await ctx.send(setup_questions[0][1])
            game.message_collection.append(sent_msg)

            try:
                msg = await client.wait_for("message", check=check_channel)
                if msg:
                    setup_chan = await TextChannelConverter().convert(ctx, msg.content)
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid Text Channel. Try again!")
                game.message_collection.append(sent_msg)
            else:
                chan_setup = False

        timer_setup = True
        while timer_setup:
            sent_msg = await ctx.send(setup_questions[1][1])
            game.message_collection.append(sent_msg)

            try:
                msg = await client.wait_for("message", check=check_timer_and_questions)
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
                msg = await client.wait_for("message", check=check_timer_and_questions)
                if not msg == "N/A":
                    setup_question_length = abs(int(msg.content))
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid number of questions. Try again!")
                game.message_collection.append(sent_msg)
            else:
                question_length_setup = False

        category_setup = True
        while category_setup:
            sent_msg = await ctx.send(setup_questions[3][1])
            game.message_collection.append(sent_msg)

            try:
                msg = await client.wait_for("message", check=check_category)
                if msg:
                    setup_category = trivia_cats[msg.clean_content]
            except TimeoutError:
                print("A Timeout Error occurred.")
            except discord.ext.commands.BadArgument:
                sent_msg = await ctx.send("Not a valid category. Try again!")
                game.message_collection.append(sent_msg)
            else:
                category_setup = False

        game.setup(ctx.message.author, setup_chan, setup_timer, setup_question_length, setup_category)

        msg = await ctx.send(
            embed=trivia_embed(
                ["Status", "Setup Completed! React 🆗 to start the game or use `$trivia start`."],
                ["Channel", game.channel.mention],
                ["Timer", game.timer],
                ["Number of Questions", len(game.questions)],
                ["Category", game.category]
            )
        )
        game.message_collection.append(msg)

        await msg.add_reaction("🆗")

        def check_reaction(r, u):
            return u == game.trivia_master and str(r.emoji) == "🆗"

        try:
            reaction, user = await client.wait_for("reaction_add", check=check_reaction)
        except asyncio.TimeoutError:
            await ctx.send("ur dumb lol")
        else:
            await start_messages()

    @trivia.command()
    # @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    async def start(self, ctx):
        """Admin/Trivia Boss Command: Starts the trivia game"""
        if not ctx.message.author == game.trivia_master:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["trivia_master"]]
                )
            )
            return

        await start_messages()

    @trivia.command(aliases=["n",], hidden=True)
    # @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
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
    # @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    async def quit(self, ctx):
        """Admin/Trivia Boss Command: Quit the current trivia game"""
        if game.setup_complete:
            await quit_game()
        else:
            await ctx.send(
                embed=trivia_embed(
                    ["Error!", errors["not_setup"]]
                )
            )

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
