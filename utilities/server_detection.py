import sys


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
