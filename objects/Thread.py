import asyncio
import datetime
import enum
import re
from typing import Coroutine

from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["wait_and_run"]

logger.info(f"{str(__name__).title()} module loaded!")


class DateTimeChars(enum.Enum):
    def __str__(self):
        return str(self.value)

    DAY = "d"
    HOUR = "h"
    MINUTE = "m"
    SECOND = "s"


def getDateTimeValue(dt_get: str, dt_string: str) -> int:
    if dt_get not in dt_string:
        return 0

    raw = dt_string.split(dt_get)[0]
    if raw.isnumeric():
        return int(raw)
    else:
        findall = re.findall(r"\D", raw)[-1]
        return int(raw[raw.find(findall) + 1 :]) or 0


# TODO Make this into a class and add other functions.
async def wait_and_run(duration: datetime.timedelta, func: Coroutine) -> None:
    logger.info(f"Waiting {duration.total_seconds()} seconds to run {func.__name__}")
    await asyncio.sleep(delay=duration.total_seconds())
    logger.info(f"{func.__name__} waiting complete. Calling funciton!")
    result = await func
