import asyncio
import enum
import re
from datetime import datetime, timedelta
from typing import Coroutine, Optional, Callable, Union

from helpers.constants import DT_TASK_FORMAT
from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__: list[str] = [
    "DateTimeChars",
    "background_run_function",
    "convertDateTimeString",
    "convert_duration",
    "prettifyTimeDateValue",
]


class DateTimeChars(enum.Enum):
    def __str__(self) -> str:
        return str(self.value)

    DAY = "d"
    HOUR = "h"
    MINUTE = "m"
    SECOND = "s"


def prettifyTimeDateValue(total_seconds: float) -> str:
    total_seconds: int = int(total_seconds)
    days, total_seconds = divmod(total_seconds, 86400)
    hours, total_seconds = divmod(total_seconds, 3600)
    minutes, total_seconds = divmod(total_seconds, 60)
    if days > 0:
        return f"{days:,}d, {hours}h, {minutes}m, and {total_seconds}s"
    elif hours > 0:
        return f"{hours}h, {minutes}m, and {total_seconds}s"
    elif minutes > 0:
        return f"{minutes}m and {total_seconds}s"
    else:
        return f"{total_seconds}s"


def getDateTimeValue(dt_get: str, dt_string: str) -> int:
    if dt_get not in dt_string:
        return 0

    raw: str = dt_string.split(dt_get)[0]
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
    imported_datetime: datetime = datetime.strptime(value, DT_TASK_FORMAT)
    dt_now: datetime = datetime.now()

    if imported_datetime > dt_now:
        duration: timedelta = imported_datetime - dt_now
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
        logger.info(f"{func.__name__} waiting complete. Calling function!")

    result = await func


logger.info(f"{str(__name__).title()} module loaded!")
