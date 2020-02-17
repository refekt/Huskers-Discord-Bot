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

    guild = await client.fetch_guild(440632686185414677)
    guild_members = await guild.fetch_members()

    admin_or_mods = []

    for member in guild_members:
        if ROLE_ADMIN_PROD == member.top_role.id or ROLE_MOD_PROD == member.top_role.id:
            admin_or_mods.append(member)

    return repr(admin_or_mods)

    # names = ["0"]
    # animals = ["z"]
    # mammals = dict()
    # i = 0
    # for name in names:
    #     hash_object = hashlib.md5(name.encode())
    #     mammals.update({animals[i]: hash_object.hexdigest()})
    #     i += 1
    #
    # print(mammals)

if __name__ == "__main__":
    import asyncio

    asyncio.run(makeMD5())
