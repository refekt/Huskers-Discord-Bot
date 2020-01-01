import sys

from unidecode import unidecode


def remove_non_ascii(text):
    return unidecode(str(text))


def bot_latency():
    from utils.client import client
    return client.latency / 100


def on_prod_server():
    return True if sys.argv[1] == "prod" else False