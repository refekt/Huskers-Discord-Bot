import asyncio
import enum
import logging
import random
import time
from datetime import datetime, time as _time
from typing import ClassVar

import discord
import requests
import schedule

from helpers.constants import (
    DEBUGGING_CODE,
    HEADERS,
    SCHED_DAY_IMG,
    SCHED_NIGHT_IMG,
    TZ,
    WEATHER_API_KEY,
)
from helpers.embed import buildEmbed
from helpers.misc import shift_utc_tz
from objects.Logger import discordLogger
from objects.Weather import WeatherResponse

asyncio_logger = discordLogger(
    name="asyncio", level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = ["SchedulePosts"]


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


class SchedulePosts:
    __slots__ = [
        "_day_delivery_time",
        "_night_delivery_time",
        "_setup",
        "channel",
        "is_day",
        "is_night",
        "schedule_daily_embeds",
        "schedule_embeds",
        "schedule_nightly_embeds",
        "schedule_random_embed",
        "send_message",
        "which_day",
    ]

    def __init__(self, channel: discord.TextChannel) -> None:
        asyncio_logger.debug("Creating SchedulePosts instance")

        description_daily: ClassVar[str] = "MORNING GANG RISE UP!"
        description_nightly: ClassVar[str] = "Night Owls Assemble!"
        title_daily: ClassVar[str] = "Daily Themed Topics of Discussion"
        title_nightly: ClassVar[str] = "Nightly Themed Topics of Discussion"

        self._day_delivery_time: time = _time(hour=7, minute=0, second=0, tzinfo=TZ)
        self._night_delivery_time: time = _time(hour=20, minute=0, second=0, tzinfo=TZ)
        self._setup: bool = False
        self.channel: discord.TextChannel = channel
        self.is_day: bool = False
        self.is_night: bool = False
        self.schedule_daily_embeds: list[discord.Embed] = [
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Monday Motivation",
                        value=f"Monday's suck. How can get through the day?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Good News Tuesday",
                        value=f"Share your good news of the day/week!",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"What's Your Wish Wednesday",
                        value=f"What do you want to see happen this week?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Throwback Thursday",
                        value=f"What is something from the past you want to share?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Finally Friday",
                        value=f"What's the plan for the weekend?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Saturday",
                        value=f"Weekend vibes. Possibly CFB game day?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
            buildEmbed(
                title=title_daily,
                description=description_daily,
                fields=[
                    dict(
                        name=f"Sunday",
                        value=f"Weekend vibes. Possibly NFL game day?",
                    )
                ],
                image=SCHED_DAY_IMG,
            ),
        ]
        self.schedule_nightly_embeds: list[discord.Embed] = [
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Mellow Monday",
                        value=f"Monday night relaxation",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Thriving Tuesday",
                        value=f"Share your good news of the day/week!",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Worry-free Wednesday",
                        value=f"What has made this week good?",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Thirsty Thursday",
                        value=f"DRINKS?",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Freedom Friday",
                        value=f"Free as a bird, flying over mountains",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Saturday",
                        value=f"Weekend vibes. Possibly CFB post-game day?",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
            buildEmbed(
                title=title_nightly,
                description=description_nightly,
                fields=[
                    dict(
                        name=f"Sunday",
                        value=f"Weekend vibes. Possibly NFL post-game day?",
                    )
                ],
                image=SCHED_NIGHT_IMG,
            ),
        ]
        self.schedule_embeds: list[list[discord.Embed], list[discord.Embed]] = [
            self.schedule_daily_embeds,
            self.schedule_nightly_embeds,
        ]
        self.schedule_random_embed: list[discord.Embed] = [
            buildEmbed(
                title="All Praise the Meme Overlord Gumby",
                description="May his ways never be forgotten!",
                image="https://i.imgur.com/BGFD6Fk.jpg",
            ),
            buildEmbed(
                title="OVERTHROW THE REDNAMES",
                description="Rednames suck",
                image="https://i.imgur.com/2ciD4Va.jpg",
            ),
        ]
        self.send_message: bool = False
        self.which_day: int = 0

        asyncio_logger.debug("SchedulePosts initialized")

    def send_daily_message(self, is_day: bool = False, is_night: bool = False) -> None:
        asyncio_logger.info("Attempting to send a daily message")
        self.send_message = True
        self.is_day = is_day
        self.is_night = is_night

        dt_now = datetime.now(tz=TZ)
        self.which_day = dt_now.weekday()

    def _setup_debug_schedule(self) -> None:
        asyncio_logger.debug("Creating schedule for debug messages")

        schedule.every(5).seconds.do(
            self.send_daily_message, is_day=True, is_night=False
        )

        all_jobs: list[schedule.Job] = schedule.jobs
        all_jobs_str: str = ""
        for job in all_jobs:
            all_jobs_str += f"* {repr(job)}\n"
        asyncio_logger.info(f"Scheduled messages complete. Jobs are:\n\n{all_jobs_str}")

        asyncio_logger.debug("Scheduled debug messages for every 3 seconds")

    def _setup_schedule(self) -> None:
        asyncio_logger.debug("Creating schedule for daily posts")

        day_time_str: str = (
            f"{self._day_delivery_time.hour:02d}:{self._day_delivery_time.minute:02d}"
        )
        night_time_str: str = f"{self._night_delivery_time.hour:02d}:{self._night_delivery_time.minute:02d}"
        asyncio_logger.debug(
            f"Day time string is {day_time_str}. Night time string is {night_time_str}."
        )

        # Get sunrise and sunset
        weather_url: str = f"https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API_KEY}&units=imperial&lang=en&q=Omaha,NE,US"
        response: requests.Response = requests.get(weather_url, headers=HEADERS)
        response.json()
        j: dict[str, ...] = response.json()

        if j:
            weather: WeatherResponse = WeatherResponse(j)

            sunrise: datetime = shift_utc_tz(weather.sys.sunrise, weather.timezone)
            sunrise_str: str = f"{sunrise.astimezone(tz=TZ).hour:02d}:{sunrise.astimezone(tz=TZ).minute:02d}"
            asyncio_logger.debug(f"Sunrise: {sunrise_str}")

            sunset: datetime = shift_utc_tz(weather.sys.sunset, weather.timezone)
            sunset_str: str = f"{sunset.astimezone(tz=TZ).hour:02d}:{sunset.astimezone(tz=TZ).minute:02d}"
            asyncio_logger.debug(f"Sunset: {sunset_str}")

            schedule.every().day.at(sunrise_str).do(
                self.send_daily_message,
                is_day=True,
                is_night=False,
            )

            schedule.every().day.at(sunset_str).do(
                self.send_daily_message,
                is_day=False,
                is_night=True,
            )
        else:
            schedule.every().day.at(day_time_str).do(
                self.send_daily_message,
                is_day=True,
                is_night=False,
            )

            schedule.every().day.at(night_time_str).do(
                self.send_daily_message,
                is_day=False,
                is_night=True,
            )

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
                self._setup_debug_schedule()
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
        asyncio_logger.debug("Running SchedulePosts loop")

        if DEBUGGING_CODE:
            asyncio_logger.setLevel(logging.DEBUG)
        else:
            asyncio_logger.setLevel(logging.INFO)

        while True:
            schedule.run_pending()
            await asyncio.sleep(1)

            if self.send_message:
                asyncio_logger.debug("self.send_message == True")
                if random.randint(1, 100) <= 5:
                    await self.channel.send(
                        embed=random.choice(self.schedule_random_embed)
                    )
                elif self.is_day:
                    await self.channel.send(
                        embed=self.schedule_daily_embeds[self.which_day]
                    )
                elif self.is_night:
                    await self.channel.send(
                        embed=self.schedule_nightly_embeds[self.which_day]
                    )

                self.is_day = False
                self.is_night = False
                self.send_message = False
            else:
                asyncio_logger.debug("self.send_message == False")


asyncio_logger.info(f"{str(__name__).title()} module loaded!")
