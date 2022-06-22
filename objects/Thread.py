import asyncio
import enum
import re
from datetime import datetime, timedelta
from typing import Coroutine, Optional, Callable, Union

from helpers.constants import DT_TASK_FORMAT
from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = [
    "DateTimeChars",
    "convertDateTimeString",
    "convert_duration",
    "prettifyTimeDateValue",
    "background_run_function",
]

logger.info(f"{str(__name__).title()} module loaded!")


class DateTimeChars(enum.Enum):
    def __str__(self):
        return str(self.value)

    DAY = "d"
    HOUR = "h"
    MINUTE = "m"
    SECOND = "s"


def prettifyTimeDateValue(seconds) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return f"{days:,}D {hours}H, {minutes}M, and {seconds}S"
    elif hours > 0:
        return f"{hours}H, {minutes}M, and {seconds}S"
    elif minutes > 0:
        return f"{minutes}M and {seconds}S"
    else:
        return f"{seconds}S"


def getDateTimeValue(dt_get: str, dt_string: str) -> int:
    if dt_get not in dt_string:
        return 0

    raw = dt_string.split(dt_get)[0]
    if raw.isnumeric():
        return int(raw)
    else:
        findall = re.findall(r"\D", raw)[-1]
        return int(raw[raw.find(findall) + 1 :]) or 0


def convertDateTimeString(dt_string: str) -> timedelta:
    dt_days, dt_hours, dt_minutes, dt_seconds = [
        getDateTimeValue(dt.__str__(), dt_string) for dt in DateTimeChars
    ]

    return timedelta(
        days=dt_days, hours=dt_hours, minutes=dt_minutes, seconds=dt_seconds
    )


def convert_duration(value: str) -> timedelta:
    imported_datetime = datetime.strptime(value, DT_TASK_FORMAT)
    dt_now = datetime.now()

    if imported_datetime > dt_now:
        duration = imported_datetime - dt_now
        return duration
    return timedelta(seconds=0)


async def background_run_function(
    func: Union[Coroutine, Callable], duration: Optional[timedelta] = None
) -> None:
    if duration:
        logger.info(
            f"Waiting {duration.total_seconds()} seconds to run {func.__name__}"
        )
        await asyncio.sleep(delay=duration.total_seconds())
        logger.info(f"{func.__name__} waiting complete. Calling funciton!")

    result = await func
