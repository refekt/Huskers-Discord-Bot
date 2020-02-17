import hashlib
import sys

from unidecode import unidecode


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
    animals = ["aardvark", "leopard", "baboon", "meerkat", "bobcat", "meerkat", "cheetah", "ocelot", "dingo", "platypus", "skunk", "squirrel", "horse", "koala", "zebra", "wolf", "fox", "giraffe", "leopard", "raccoon", "elephant", "cat", "dog"]
    mammals = {}

    for member in guild_members:
        if ROLE_ADMIN_PROD == member.top_role.id or ROLE_MOD_PROD == member.top_role.id:
            admin_or_mods.append(member)

    for index, who in enumerate(admin_or_mods):
        hash_object = hashlib.md5(str(who.id).encode())
        mammals.update({animals[index]: hash_object.hexdigest()})

    print(mammals)
