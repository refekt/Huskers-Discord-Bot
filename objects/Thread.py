import asyncio
from typing import Coroutine

from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["wait_and_run"]

logger.info(f"{str(__name__).title()} module loaded!")


# TODO Make this into a class and add other functions.
async def wait_and_run(duration: float, func: Coroutine) -> None:
    logger.info(f"Waiting {duration} seconds to run {func.__name__}")
    await asyncio.sleep(delay=duration)
    logger.info(f"{func.__name__} waiting complete. Calling funciton")

    result = await func
