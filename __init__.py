import sys
import logging
from time import perf_counter

logging.basicConfig(
    format="%(asctime)s :: %(name)s/%(levelname)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s",
    datefmt="%Y-%m-%d-%H%M%z",
    level=logging.INFO,
    encoding="utf-8",
    stream=sys.stdout,
)

start = perf_counter()

# Client
from client import *  # noqa

# Helper Functions
from helpers.constants import *  # noqa
from helpers.embed import *  # noqa
from helpers.encryption import *  # noqa
from helpers.fryer import *  # noqa
from helpers.misc import *  # noqa
from helpers.mysql import *  # noqa
from helpers.slowking import *  # noqa

# Objects/classes
from objects.Bets import *  # noqa
from objects.Exceptions import *  # noqa
from objects.Karma import *  # noqa
from objects.Prediction import *  # noqa
from objects.Recruits import *  # noqa
from objects.Schedule import *  # noqa
from objects.Thread import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

# Star the bot
logger = logging.getLogger(__name__)
end = perf_counter()
logger.info(f"The bot initialized in {end - start:,.2f} seconds")
logger.info("Starting the bot!")
bot.start()
