import asyncio
from typing import Coroutine, Any

from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["wait_and_run"]

logger.info(f"{str(__name__).title()} module loaded!")


def wait_and_run(duration: float, func: Coroutine[Any, Any, None]) -> None:
    logger.info(f"Waiting {duration} seconds to run {func.__name__}")
    asyncio.sleep(delay=duration)
    logger.info(f"{func.__name__} waiting complete. Calling funciton")
    asyncio.run(func)
