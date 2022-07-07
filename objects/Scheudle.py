import enum
import logging
import time
from datetime import datetime, time as _time

import discord
import schedule

from helpers.constants import TZ, DEBUGGING_CODE
from helpers.embed import buildEmbed

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
        asyncio_logger.debug(f"Returning {self.value} from Weekday IntEnum")
        return str(self.value)

    def __repr__(self) -> str:
        asyncio_logger.debug(f"Returning {self.value} from Weekday IntEnum")
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
        asyncio_logger.debug("Creating ScheudlePosts instance")

        self._delivery_time: time = _time(hour=7, minute=0, second=0, tzinfo=TZ)
        self._setup: bool = False
        self.channel: discord.TextChannel = channel
        self.send_message: bool = False
        self.which_day: int = 0
        self.schedule_daily_embeds: list[discord.Embed] = [
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name="fMonday Motivation",
                        value=f"Monday's suck. How can get through the day?",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"Good News Tuesday",
                        value=f"Share your good news of the day/week!",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"What's Your Wish Wednesday",
                        value=f"What do you want to see happen this week?",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"Throwback Thursday",
                        value=f"What is something from the past you want to share?",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"Finally Friday",
                        value=f"What's the plan for the weekend?",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"Saturday",
                        value=f"Weekend vibes. Possibly CFB game day?",
                    )
                ],
            ),
            buildEmbed(
                title="Daily Theme Post",
                fields=[
                    dict(
                        name=f"Sunday",
                        value=f"Weekend vibes. Possibly NFL game day?",
                    )
                ],
            ),
        ]

        asyncio_logger.debug("ScheudlePosts initialized")

    def send_daily_message(self) -> None:
        asyncio_logger.info("Attempting to send a daily message")
        self.send_message = True
        dt_now = datetime.now(tz=TZ)
        self.which_day = dt_now.weekday()

    def _setup_debug_scheudle(self) -> None:
        asyncio_logger.debug("Creating schedule for debug messages")

        schedule.every(5).seconds.do(self.send_daily_message)

        all_jobs: list[schedule.Job] = schedule.jobs
        all_jobs_str: str = ""
        for job in all_jobs:
            all_jobs_str += f"* {repr(job)}\n"
        asyncio_logger.debug(
            f"Scheduled messages complete. Jobs are:\n\n{all_jobs_str}"
        )

        asyncio_logger.debug("Scheduled debug messages for every 3 seconds")

    def _setup_schedule(self) -> None:
        asyncio_logger.debug("Creating schedule for daily posts")

        time_str: str = (
            f"{self._delivery_time.hour:02d}:{self._delivery_time.minute:02d}"
        )
        asyncio_logger.debug(f"Time string is {time_str}")

        schedule.every().day.at(time_str).do(self.send_daily_message)

        all_jobs: list[schedule.Job] = schedule.jobs
        all_jobs_str: str = ""
        for job in all_jobs:
            all_jobs_str += f"* {repr(job)}\n"
        asyncio_logger.debug(
            f"Scheduled messages complete. Jobs are:\n\n{all_jobs_str}"
        )

    def setup_and_run_schedule(self) -> None:
        if DEBUGGING_CODE:
            asyncio_logger.debug("Attempting to create debug schedule")
            if not self._setup:
                self._setup_debug_scheudle()
                self._setup = True
                asyncio_logger.debug("Debug schedule created")
            schedule.run_pending()
        else:
            asyncio_logger.debug("Attempting to create schedule")
            if not self._setup:
                self._setup_schedule()
                self._setup = True
                asyncio_logger.debug("Sschedule created")

    async def run(self):
        asyncio_logger.debug("Running ScheudlePosts loop")

        if DEBUGGING_CODE:
            asyncio_logger.setLevel(logging.DEBUG)
        else:
            asyncio_logger.setLevel(logging.INFO)

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


asyncio_logger.info(f"{str(__name__).title()} module loaded!")
