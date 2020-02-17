import hashlib
import sys

from unidecode import unidecode


def remove_non_ascii(text):
    return unidecode(str(text))


def bot_latency():
    from utils.client import client
    return client.latency / 100


def on_prod_server():
    if sys.argv[1] == "prod":
        return True
    elif sys.argv[1] == "test":
        return False
    else:
        return 0


def makeMD5():
    names = ["0"]
    animals = ["z"]
    mammals = dict()
    i = 0
    for name in names:
        hash_object = hashlib.md5(name.encode())
        mammals.update({animals[i]: hash_object.hexdigest()})
        i += 1

    print(mammals)
