import enum
import logging
import time
from datetime import datetime, time as _time

import discord
import schedule

from helpers.constants import TZ, DEBUGGING_CODE
from helpers.embed import buildEmbed
from objects.Logger import discordLogger

logger = discordLogger(__name__)
asyncio_logger = logging.getLogger("asyncio")


__all__: list[str] = ["ScheudlePosts"]


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


class ScheudlePosts:
    __slots__ = [
        "_delivery_time",
        "_setup",
        "channel",
        "schedule_daily_embeds",
        "send_message",
        "which_day",
    ]

    def __init__(self, channel: discord.TextChannel) -> None:
        logger.debug("Creating ScheudlePosts instance")

        self._delivery_time: time = _time(hour=7, minute=30, second=0, tzinfo=TZ)
        self._setup: bool = False
        self.channel: discord.TextChannel = channel
        self.send_message: bool = False
        self.which_day: int = 0
        self.schedule_daily_embeds: list[discord.Embed] = [
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

        logger.debug("ScheudlePosts initialized")

    def send_daily_message(self) -> None:
        logger.info("Attempting to send a daily message")
        self.send_message = True
        dt_now = datetime.now(tz=TZ)
        self.which_day = dt_now.weekday()

    def _setup_debug_scheudle(self) -> None:
        logger.debug("Creating schedule for debug messages")
        schedule.every(5).seconds.do(self.send_daily_message)
        logger.debug("Scheduled debug messages for every 3 seconds")

    def _setup_schedule(self) -> None:
        logger.debug("Creating schedule for daily posts")

        time_str: str = (
            f"{self._delivery_time.hour:02d}:{self._delivery_time.minute:02d}"
        )
        logger.debug(f"Time string is {time_str}")

        schedule.every().monday.at(time_str).do(self.send_daily_message)
        schedule.every().tuesday.at(time_str).do(self.send_daily_message)
        schedule.every().wednesday.at(time_str).do(self.send_daily_message)
        schedule.every().thursday.at(time_str).do(self.send_daily_message)
        schedule.every().friday.at(time_str).do(self.send_daily_message)
        schedule.every().saturday.at(time_str).do(self.send_daily_message)
        schedule.every().sunday.at(time_str).do(self.send_daily_message)

        logger.info("Scheduled messages complete")

    def setup_and_run_schedule(self) -> None:
        if DEBUGGING_CODE:
            logger.debug("Attempting to create debug schedule")
            if not self._setup:
                self._setup_debug_scheudle()
                self._setup = True
                logger.debug("Debug schedule created")
            schedule.run_pending()
        else:
            logger.debug("Attempting to create schedule")
            if not self._setup:
                self._setup_schedule()
                self._setup = True
                logger.debug("Sschedule created")
            schedule.run_pending()
            all_jobs: list[schedule.Job] = schedule.jobs()
            logger.debug(f"Jobs are:\n{[job for job in all_jobs]}")

    async def run(self):
        if DEBUGGING_CODE:
            asyncio_logger.setLevel(logging.DEBUG)
        else:
            asyncio_logger.setLevel(logging.INFO)

        asyncio_logger.debug("Running ScheudlePosts loop")
        while True:
            schedule.run_pending()
            time.sleep(1)

            if self.send_message:
                asyncio_logger.debug("self.send_message == True")
                await self.channel.send(
                    embed=self.schedule_daily_embeds[self.which_day]
                )
                self.send_message = False
            else:
                asyncio_logger.debug("self.send_message == False")


logger.info(f"{str(__name__).title()} module loaded!")
