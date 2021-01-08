import hashlib
import sys
import json

from cryptography.fernet import Fernet
from unidecode import unidecode


# https://github.com/x4nth055/pythoncode-tutorials/blob/master/ethical-hacking/file-encryption/crypt.py

def write_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """
    Loads the key from the current directory named `key.key`
    """
    return open("key.key", "rb").read()


def encrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it encrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read all file data
        file_data = file.read()
    # encrypt data
    encrypted_data = f.encrypt(file_data)
    # write the encrypted file
    with open(filename, "wb") as file:
        file.write(encrypted_data)


def decrypt_return_data(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    decrypted_data = json.loads(decrypted_data)

    return decrypted_data


def decrypt(filename, key):
    """
    Given a filename (str) and key (bytes), it decrypts the file and write it
    """
    f = Fernet(key)
    with open(filename, "rb") as file:
        # read the encrypted data
        encrypted_data = file.read()
    # decrypt data
    decrypted_data = f.decrypt(encrypted_data)
    # write the original file
    with open(filename, "wb") as file:
        file.write(decrypted_data)


# def remove_mentions(message):
#     return str(message).replace("<", "[User: ").replace("@!", "").replace(">", "]")


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

#Takes a string and delimeter and returns a list of values between the delimiters
def seperArgs(arg,delimeter):
    finalArgs = []
    toAppend = ''
    index = 0
    for i in arg:
        if(i == delimeter):
            finalArgs.append(toAppend.strip())
            toAppend = ''
        else:
            toAppend += i
        if(index == len(arg) - 1):
            finalArgs.append(toAppend.strip())
            toAppend = ''
        index += 1
    return finalArgs

# async def send_message(when, who: typing.Union[discord.Member, discord.TextChannel], what, extra=None):
#     print("send message, sleeping")
#     await asyncio.sleep(when)
#     print("slept")
#     if not when == 0:
#         await who.send(f"[Reminder for {who.mention}]: {remove_mentions(what)}")
#         # process_MySQL(sqlUpdateTasks, values=(0, who.id, what, when))
#         process_MySQL(sqlUpdateTasks, values=(0, who.id, what, str(extra)))
#     else:
#         imported_datetime = datetime.strptime(extra, "%Y-%m-%d %H:%M:%S.%f")
#         await who.send(f"[Missed reminder for [{who.mention}] set for [{imported_datetime.strftime('%x %X')}]!]: {remove_mentions(what)}")
#         process_MySQL(sqlUpdateTasks, values=(0, who.id, what, str(extra)))
