import typing
from threading import Timer

import discord


async def send_message(who: typing.Union[discord.Member, discord.TextChannel], what: str):
    await who.send(what)


def start_timer_for(duration: int, who: typing.Union[discord.Member, discord.TextChannel], what: str):
    timer = Timer(duration, send_message(who=who, what=what))
    timer.start()
