import asyncio
import hashlib
import sys
import typing
from datetime import datetime

import discord
from unidecode import unidecode

from utils.mysql import process_MySQL, sqlUpdateTasks


def remove_mentions(message):
    return str(message).replace("<", "[User: ").replace("@!", "").replace(">", "]")


def remove_non_ascii(text):
    return unidecode(str(text))


def bot_latency():
    from utils.client import client
    return client.latency / 100


def on_prod_server():
    try:
        if sys.argv[1] == "prod":
            return True
        elif sys.argv[1] == "test":
            return False
        else:
            return 0
    except IndexError:
        return False


async def makeMD5():
    from utils.consts import ROLE_MOD_PROD, ROLE_ADMIN_PROD
    from utils.client import client

    guild = client.guilds[1]
    guild_members = guild.members

    admin_or_mods = []
    animals = ["aardvark", "leopard", "baboon", "meerkat", "bobcat", "meerkat", "cheetah", "ocelot", "dingo", "platypus", "skunk", "squirrel", "horse", "koala", "zebra", "wolf", "fox", "giraffe",
               "leopard", "raccoon", "elephant", "cat", "dog"]
    mammals = {}

    for member in guild_members:
        if ROLE_ADMIN_PROD == member.top_role.id or ROLE_MOD_PROD == member.top_role.id:
            admin_or_mods.append(member)

    for index, who in enumerate(admin_or_mods):
        hash_object = hashlib.md5(str(who.id).encode())
        mammals.update({animals[index]: hash_object.hexdigest()})

    print(mammals)


async def send_message(when, who: typing.Union[discord.Member, discord.TextChannel], what, extra=None):
    await asyncio.sleep(when)
    if not when == 0:
        await who.send(f"[Reminder for {who.mention}]: {remove_mentions(what)}")
        # process_MySQL(sqlUpdateTasks, values=(0, who.id, what, when))
        process_MySQL(sqlUpdateTasks, values=(0, who.id, what, str(extra)))
    else:
        imported_datetime = datetime.strptime(extra, "%Y-%m-%d %H:%M:%S.%f")
        await who.send(f"[Missed reminder for [{who.mention}] set for [{imported_datetime.strftime('%x %X')}]!]: {remove_mentions(what)}")
        process_MySQL(sqlUpdateTasks, values=(0, who.id, what, str(extra)))
