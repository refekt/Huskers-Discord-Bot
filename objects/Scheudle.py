import enum
from datetime import time

import discord
import schedule

from helpers.constants import TZ, DEBUGGING_CODE
from helpers.embed import buildEmbed
from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["ScheudlePosts"]


class Weekday(enum.IntEnum):
    monday = 0
    tuesday = 1
    wednesday = 2
    thursday = 3
    friday = 4
    saturday = 5
    sunday = 6

    def __str__(self) -> str:
        logger.debug(f"Returning {self.value} from Weekday IntEnum")
        return str(self.value)

    def __repr__(self) -> str:
        logger.debug(f"Returning {self.value} from Weekday IntEnum")
        return str(self.value)


async def send_daily_message(
    channel: discord.TextChannel, embed: discord.Embed
) -> None:
    logger.info(f"Sending a daily message to {channel.name}")
    await channel.send(embed=embed)


class ScheudlePosts:
    __slots__ = [
        "_delivery_time",
        "_embeds",
    ]

    def __init__(
        self,
    ) -> None:
        self._delivery_time: time = time(hour=7, minute=30, second=0, tzinfo=TZ)
        self._embeds: list[discord.Embed] = [
            buildEmbed(
                title=f"Monday Motivation",
                description=f"Monday's suck. How can get through the day?",
            ),
            buildEmbed(
                title=f"Good News Tuesday",
                description=f"Share your good news of the day/week!",
            ),
            buildEmbed(
                title=f"What's Your Wish Wednesday",
                description=f"What do you want to see happen this week?",
            ),
            buildEmbed(
                title=f"Throwback Thursday",
                description=f"What is something from the past you want to share?",
            ),
            buildEmbed(
                title=f"Finally Friday",
                description=f"What's the plan for the weekend?",
            ),
            buildEmbed(title=f"Saturday", description=f"Weekend vibes"),
            buildEmbed(title=f"Sunday", description=f"Weekend vibes"),
        ]

    # noinspection PyMethodMayBeStatic
    def _setup_debug_scheudle(self) -> None:
        logger.debug("Creating schedule for debug messages")
        debug_job = schedule.every(3).seconds.do(print, "Debug message for schedule")
        logger.debug("Scheduled debug messages for every 3 seconds")

    def _setup_schedule(self) -> None:
        logger.info("Creating schedule for daily posts")

        time_str: str = (
            f"{self._delivery_time.hour:02d}:{self._delivery_time.minute:02d}"
        )
        logger.debug(f"Time string is {time_str}")

        schedule.every().monday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.monday]
        )
        schedule.every().tuesday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.tuesday]
        )
        schedule.every().wednesday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.wednesday]
        )
        schedule.every().thursday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.thursday]
        )
        schedule.every().friday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.friday]
        )
        schedule.every().saturday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.saturday]
        )
        schedule.every().sunday.at(time_str).do(
            send_daily_message, self._embeds[Weekday.sunday]
        )
        logger.info("Scheduled messages complete")

    def setup_and_run_schedule(self) -> None:
        if DEBUGGING_CODE:
            logger.debug("Attempting to create debug schedule")
            self._setup_debug_scheudle()
            schedule.run_pending()
        else:
            logger.debug("Attempting to create schedule")
            self._setup_schedule()
            schedule.run_pending()


logger.info(f"{str(__name__).title()} module loaded!")
