import enum
import logging

from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__, level=logging.DEBUG if is_debugging() else logging.INFO
)

__all__ = ["IowaDuration"]


class IowaDuration(enum.IntEnum):
    _30_min = 30
    _1_hour = 60
    _12_hour = _1_hour * 12
    _1_day = _1_hour * 24
    _2_day = _1_day * 2
    _3_day = _1_day * 3
    _4_day = _1_day * 4
    _5_day = _1_day * 5
    _6_day = _1_day * 6
    _1_week = _1_day * 7
    _2_week = _1_week * 2
    _3_week = _1_week * 3
    _1_month = _1_week * 4


logger.info(f"{str(__name__).title()} module loaded!")
