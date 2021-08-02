import sys

from utilities.constants import GUILD_PROD, GUILD_TEST


def production_server():
    try:
        if sys.argv[1] == "prod":
            return True
        elif sys.argv[1] == "test":
            return False
        else:
            return None
    except IndexError:
        return None


def which_guid():
    if production_server():
        return GUILD_PROD
    else:
        return GUILD_TEST
