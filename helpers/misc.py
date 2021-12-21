import pathlib
import platform
import random
import string

import interactions

from objects.Exceptions import CommandException, UserInputException


def log(level: int, message: str):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Misc: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Misc: {message}")


def formatPrettyTimeDelta(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return f"{days:,}D {hours}H, {minutes}M, and {seconds}S"
    elif hours > 0:
        return f"{hours}H, {minutes}M, and {seconds}S"
    elif minutes > 0:
        return f"{minutes}M and {seconds}S"
    else:
        return f"{seconds}S"


def grabPlatform():
    return platform.platform()


def loadVarPath() -> [str, CommandException]:
    p = platform.platform()
    if "Windows" in p:
        log(0, f"Windows environment set")
        return pathlib.PurePath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/variables.json"
        )
    elif "Linux" in p:
        log(0, f"Linux environment set")
        return pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/variables.json"
        )
    else:
        return CommandException(f"Unable to support {platform.platform()}!")


def createComponentKey() -> str:
    return "".join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(10)
    )


def getUserMention(user: interactions.User) -> [str, UserInputException]:
    if not type(user) == interactions.User:
        return UserInputException("An `interactions.User` was not provided!")
    else:
        return f"<@{user.id}>"


async def getCurrentGuildID(bot: interactions.Client) -> int:
    g = await bot.http.get_self_guilds()
    return int(g[0]["id"])


async def getGuild(bot: interactions.Client, gID: int) -> interactions.Guild:
    return interactions.Guild(**(await bot.http.get_guild(guild_id=gID)))


async def getBotUser(bot: interactions.Client):
    return interactions.User(**(await bot.http.get_self()))
