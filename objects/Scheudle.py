import asyncio
import enum
import logging
import random
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

    @property
    def __weather_info(self) -> WeatherResponse:
        weather_url: str = f"https://api.openweathermap.org/data/2.5/weather?appid={WEATHER_API_KEY}&units=imperial&lang=en&q=Omaha,NE,US"
        response: requests.Response = requests.get(weather_url, headers=HEADERS)
        response.json()
        j: dict[str, ...] = response.json()

        return WeatherResponse(j)

    @property
    def sunrise_str(self) -> str:
        try:
            sunrise = self.__weather_info.sys.sunrise
        except requests.exceptions.RequestException:
            sunrise = _time(hour=7, minute=0, second=0, tzinfo=TZ)

        return f"{sunrise.hour :02d}:{sunrise.minute:02d}"

    @property
    def sunset_str(self) -> str:
        try:
            sunset = self.__weather_info.sys.sunset
        except requests.exceptions.RequestException:
            sunset = _time(hour=10, minute=0, second=0, tzinfo=TZ)

        return f"{sunset.hour :02d}:{sunset.minute:02d}"

    def send_daily_message(self, is_day: bool = False, is_night: bool = False) -> None:
        asyncio_logger.info("Attempting to send a daily message")

        self.send_message = True
        self.is_day = is_day
        self.is_night = is_night
        self.which_day = datetime.now(tz=TZ).weekday()

    @property
    def all_jobs(self) -> str:
        all_jobs: list[schedule.Job] = schedule.jobs
        all_jobs_str: str = ""
        for job in all_jobs:
            all_jobs_str += f"* {repr(job)}\n"

        return all_jobs_str

    def _setup_debug_schedule(self) -> None:
        asyncio_logger.debug("Creating schedule for debug messages")

        schedule.every(5).seconds.do(
            self.send_daily_message, is_day=True, is_night=False
        )

        asyncio_logger.info(
            f"Scheduled messages complete. Jobs are:\n\n{self.all_jobs}"
        )

    def _setup_schedule(self) -> None:
        asyncio_logger.debug(
            "Creating schedule for daily posts from sunrise and sunset"
        )

        asyncio_logger.debug(f"Sunrise: {self.sunrise_str}")
        schedule.every().day.at(self.sunrise_str).do(
            self.send_daily_message,
            is_day=True,
            is_night=False,
        )

        asyncio_logger.debug(f"Sunset: {self.sunset_str}")
        schedule.every().day.at(self.sunset_str).do(
            self.send_daily_message,
            is_day=False,
            is_night=True,
        )

        asyncio_logger.debug(
            f"Scheduled messages complete. Jobs are:\n\n{self.all_jobs}"
        )

    def setup_and_run_schedule(self) -> None:
        asyncio_logger.debug("Clearing any previous jobs")

        for scheduled_job in schedule.jobs:
            schedule.cancel_job(scheduled_job)

        asyncio_logger.debug("Previous jobs cleared")

        if DEBUGGING_CODE:
            asyncio_logger.debug("Attempting to create debug schedule")
            if not self._setup:
                self._setup_schedule()
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
