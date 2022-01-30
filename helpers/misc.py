import logging
import pathlib
import platform
import random
import string

import interactions

from objects.Exceptions import CommandException, UserInputException

logger = logging.getLogger(__name__)

__all__ = [
    "convertEmbedtoDict",
    "createComponentKey",
    "formatPrettyTimeDelta",
    "getBotUser",
    "getChannelMention",
    "getChannelbyID",
    "getCurrentGuildID",
    "getGuild",
    "getUserMention",
    "grabPlatform",
    "loadVarPath",
]


def formatPrettyTimeDelta(seconds) -> str:
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


def grabPlatform() -> str:
    return platform.platform()


def loadVarPath() -> [str, CommandException]:
    myPlatform = platform.platform()
    if "Windows" in myPlatform:
        logger.info(f"Windows environment set")
        return pathlib.PurePath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/resources/variables.json"
        )
    elif "Linux" in myPlatform:
        logger.info(f"Linux environment set")
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
    if not isinstance(user, dict):
        return UserInputException("An `interactions.User` was not provided!")

    return f"<@{user.get('id')}>"


def getChannelMention(channel_id: int) -> [str, UserInputException]:
    if not isinstance(channel_id, int):
        return UserInputException("Must provide a value channel ID")

    return f"<#{channel_id}>"


async def getCurrentGuildID(bot: interactions.Client) -> int:
    return int(await bot._http.get_self_guilds()[0]["id"])


async def getGuild(bot: interactions.Client, gID: int) -> interactions.Guild:
    return interactions.Guild(
        **await bot._http.get_guild(guild_id=gID), _state=bot._http
    )


async def getBotUser(bot: interactions.Client):
    return interactions.User(**await bot._http.get_self(), _state=bot._http)


async def getChannelbyID(
    bot: interactions.Client, chan_id: int
) -> interactions.Channel:
    return interactions.Channel(**await bot._http.get_channel(chan_id), _client=bot._http)


def convertEmbedtoDict(embed: interactions.Embed) -> dict:
    _ = embed._json
    # _["author"] = embed.author._json
    # _["footer"] = embed.footer._json
    # _["thumbnail"] = embed.thumbnail._json
    # _["fields"] = [field._json for field in _["fields"]]
    return _


logger.info(f"{str(__name__).title()} module loaded!")
