from discord.ext import commands
import discord
import random
from enum import Enum
import typing

gaming_channels = (593984711706279937, 595705205069185047)
stages = {"new": 6, "finished": 0}
word_choices = (
    "husker",
    "nebraska",
    "skers",
    "fuqmizzou",
    "rex burkhead",
    "callahan",
    "scarlet and cream",
    "bugeaters",
    "gridiron",
    "iowegian",
    "one second",
    "team jack",
    "tommy bomb",
    "tuck fexas",
    "lincoln",
    "corn rage",
    "midwest",
    "ndamukong suh",
    "martinez",
    "sexy rexy",
    "runza",
    "frosty",
    "scott frost",
    "iowa sucks",
    "bill moos",
    "mike riley",
    "osborne",
    "go for two",
    "memorial stadium",
    "herbie",
    "lil red",
    "hail varsity",
    "man woman and child",
    "eric crouch",
    "mike rozier",
    "johnny rodgers",
    "heisman",
    "national champions",
    "the pride of all nebraska",
    "there is no place like nebraska",
    "nebraska its not for everyone",
    "adidas",
    "devaney",
    "steinkuhler",
    "orange bowl",
    "flea kicker",
    "ron kellog",
    "big eight",
    "frank solich",
    "gator bowl"
)
hangman_stages = (
    """
    ___________
    |       |
    |       0
    |      /|\\
    |      / \\
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       0
    |      /|\\
    |      / 
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       0
    |      /|\\
    |       
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       0
    |      /|
    |      
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       0
    |       |
    |      
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       0
    |       
    |      
    |
    |
    -----------
    """,
    """
    ___________
    |       |
    |       
    |       
    |      
    |
    |
    -----------
    """
)
current_word = ""
built_word = ""
players = []
guesses = []
max_moves = 6
moves_left = max_moves
keep_playing = False


class Attempts(Enum):
    correct = 1
    incorrect = 0
    duplicate = -1


class GameCondition(Enum):
    win = 1
    lose = 0
    playing = 2


def pick_new_word():
    return random.choice(word_choices)


def build_board(turn: int):
    return hangman_stages[turn]


def build_word_bar():
    global guesses
    global current_word

    word_bar = ""
    if guesses:
        for letter in current_word:
            if letter in guesses:
                word_bar += "{} ".format(letter)
            else:
                if letter == " ":
                    word_bar += " "
                else:
                    word_bar += "_ "
    else:
        for letter in current_word:
            word_bar += "_ "

    global built_word
    built_word = word_bar

    word_bar = "\nWord: " + word_bar + "\nGuesses: {}".format(guesses)

    return word_bar


def build_message():
    return "```\nHusker Hangman!\n" + build_board(moves_left) + build_word_bar() + "\n```"


def try_guess(letter: str):
    global current_word
    global guesses

    guesses.append(letter)

    if letter in current_word:
        return Attempts.correct
    elif letter in guesses:
        return Attempts.duplicate
    else:
        return Attempts.incorrect


def check_win_or_lose():
    global moves_left

    check_current_word = current_word.replace(" ", "")
    check_word_bar = built_word.replace(" ", "")

    if moves_left <= 0:
        return GameCondition.lose

    if check_current_word == check_word_bar:
        return GameCondition.win

    return GameCondition.playing


def is_in_players(checkme):
    global players
    if checkme in players:
        return True
    else:
        return False


def setup(bot):
    bot.add_cog(Hangman(bot))


class Hangman(commands.Cog, name="Husker Hangman"):
    """Husker Hangman!"""
    @commands.group(aliases=["hm",])
    async def hangman(self, ctx):
        pass

    @hangman.command(aliases=["g",])
    async def guess(self, ctx, letter: str):
        if not letter.isalpha():
            await ctx.send("Guesses must be alpha characters only!")
            return

        global keep_playing
        if not keep_playing:
            await ctx.send("There is no game currently being played. To start a new game use `$hangman new [discord.Member,...]`.")
            return

        if not is_in_players(ctx.message.author.name):
            await ctx.send("You are not a registered participant in this game!")
            return

        edit_msg = await ctx.send("Thinking...")

        letter = letter[0].lower()
        guess = try_guess(letter)

        global moves_left
        if guess == Attempts.incorrect or guess == Attempts.duplicate:
            moves_left -= 1

        await edit_msg.delete()

        async for message in ctx.channel.history(limit=100):
            if "Husker Hangman!" in message.content and message.author.bot:
                await message.delete()
                break

        await ctx.send(build_message())

        if check_win_or_lose() == GameCondition.win:
            await ctx.send("You win!")
            keep_playing = False
        elif check_win_or_lose() == GameCondition.lose:
            await ctx.send("You lose! The word was [{}].".format(current_word))
            keep_playing = False

    @hangman.command(aliases=["fg",])
    async def fullguess(self, ctx, *, word: str):
        global current_word
        global players

        if not is_in_players(ctx.message.author.name):
            await ctx.send("You are not a registered participant in this game!")
            return

        if word.lower().replace(" ", "") == current_word.replace(" ", ""):
            await ctx.send("Correct! {} wins the game!".format(ctx.author))
            global keep_playing
            keep_playing = False
        else:
            global moves_left
            global guesses
            guesses.append(word)
            moves_left -= 1
            await ctx.send(build_message())

    @hangman.command(aliases=["q",])
    async def quit(self, ctx):
        global keep_playing
        if not keep_playing:
            await ctx.send("There is no game currently being played. To start a new game use `$hangman new [discord.Member,...]`.")
            return

        if not is_in_players(ctx.message.author.name):
            await ctx.send("You are not a registered participant in this game!")

            return

        global players
        global moves_left
        global current_word
        global built_word
        global guesses

        keep_playing = False
        moves_left = max_moves
        current_word = ""
        built_word = ""
        guesses = []

        await ctx.send("The current game has been ended!")

        async for message in ctx.channel.history(limit=100):
            if "Husker Hangman!" in message.content and message.author.bot:
                await message.delete()
                break

    @hangman.command(aliases=["n",])
    async def new(self, ctx, *new_players: typing.Union[discord.Member, discord.Role]):
        if not new_players:
            await ctx.send("There must be at least one player!")
            return
        else:
            global players
            global moves_left
            global current_word
            global guesses
            global keep_playing

            keep_playing = True
            current_word = pick_new_word()
            moves_left = max_moves
            flattened = []
            players = []
            guesses = []

            for p in new_players:
                if type(p) == discord.member.Member:
                    players.append(p.name)
                    flattened.append(p.name)
                elif type(p) == discord.role.Role:
                    for member in p.members:
                        players.append(member.name)
                        flattened.append(member.name)

            await ctx.send("```\nHusker Hangman!: New game started with {}!\n```".format(flattened))

        await ctx.send(build_message())

        print("New game started with word [{}]".format(current_word))
        # await ctx.send("BETA: New game started with word [{}]".format(current_word))
