import logging
import sys
from time import perf_counter

import discord  # noqa # Beta version thing

from objects.Client import HuskerClient

logging.basicConfig(
    format="%(asctime)s :: %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s",
    datefmt="%Y-%m-%d-%H%M%z",
    level=logging.INFO,
    encoding="utf-8",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

start = perf_counter()

logger.info("Loading helpers")

# Helper Functions
from helpers.constants import *  # noqa
from helpers.embed import *  # noqa
from helpers.encryption import *  # noqa
from helpers.fryer import *  # noqa
from helpers.misc import *  # noqa
from helpers.mysql import *  # noqa
from helpers.slowking import *  # noqa

logger.info("Helpers laoded. Loading objects")

# Objects/classes
from objects.Bets import *  # noqa
from objects.Exceptions import *  # noqa
from objects.Karma import *  # noqa
from objects.Prediction import *  # noqa
from objects.Recruits import *  # noqa
from objects.Schedule import *  # noqa
from objects.Thread import *  # noqa
from objects.TweepyStreamListener import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

# Start the bot
logger.info("Objects loaded. Starting the bot!")

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client = HuskerClient(
    command_prefix=None,
    fetch_offline_members=True,
    intents=intents,
    owner_id=MEMBER_GEE,
)

end = perf_counter()
logger.info(f"The bot initialized in {end - start:,.2f} seconds")

__all__ = ["client"]


# v2.0 loop
async def main():
    async with client:
        await client.start(PROD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
