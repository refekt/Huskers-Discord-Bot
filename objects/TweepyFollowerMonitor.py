from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Optional, Callable

import discord
import tweepy
import tweepy.asynchronous
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from helpers.constants import (
    CHAN_BOT_SPAM_PRIVATE,
    CHAN_TWITTERVERSE,
    TWITTER_FOLLOWER_API_LIMIT,
    TWITTER_FOLLOWER_PAGE_REQ,
)
from helpers.embed import buildEmbed
from objects.Logger import is_debugging, discordLogger

asyncio_logger = discordLogger(
    name="asyncio", level=logging.DEBUG if is_debugging() else logging.INFO
)

following_api_calls: int = 0


class TwitterListMember:
    def __init__(
        self, client: tweepy.asynchronous.AsyncClient, twitter_user: tweepy.User
    ) -> None:
        self._client: tweepy.asynchronous.AsyncClient = client
        self.user_id: Optional[int | str] = twitter_user.id
        self.name: Optional[str] = twitter_user.name
        self.username: Optional[str] = twitter_user.username
        self.orig_followers: Optional[list[tweepy.User]] = None
        self.new_followers: Optional[list[tweepy.User]] = None

    async def get_users_following(self) -> tweepy.Response:
        global following_api_calls

        following_api_calls += 1
        asyncio_logger.debug(
            f"Total number of GET /2/users/:id/following calls: {following_api_calls}"
        )

        if following_api_calls > TWITTER_FOLLOWER_API_LIMIT:
            asyncio_logger.debug("Rate limit reached. Sleeping for 60 seconds!")
            time.sleep(60)

        return await self._client.get_users_following(
            id=self.user_id, max_results=TWITTER_FOLLOWER_PAGE_REQ
        )  # Subject to rate limiting

    async def compile(self, initial: bool = True) -> None:
        asyncio_logger.debug(
            f"Attempting to establish {'original' if initial else 'new'} user list User {self.name} (@{self.username})."
        )

        response: tweepy.Response = await self.get_users_following()
        user_list: list[tweepy.User] = response[0]

        if initial:
            self.orig_followers = user_list
        else:
            self.new_followers = user_list

        token_info: dict = response[3]
        while token_info.get("next_token", False):
            asyncio_logger.debug(
                f"User {self.name} (@{self.username}) followers required pages."
            )

            response = await self.get_users_following()

            token_info = response[3]
            user_list = response[0]

            if initial:
                self.orig_followers += user_list
            else:
                self.new_followers += user_list

        asyncio_logger.debug(
            f"Established User {self.name} (@{self.username}) {'original' if initial else 'new'} user list with {len(self.orig_followers) if initial else len(self.new_followers)} followers."
        )


class TwitterFollowerMonitor:
    def __init__(
        self,
        discord_client: discord.Client,
        tweepy_client: tweepy.asynchronous.AsyncClient,
        twitter_user: tweepy.User,
    ) -> None:
        self.discord_client: discord.Client = discord_client
        self.tweepy_client: tweepy.asynchronous.AsyncClient = tweepy_client
        self.twitter_user: TwitterListMember = TwitterListMember(
            client=self.tweepy_client, twitter_user=twitter_user
        )
        self.thread: Optional[threading.Thread] = None

        asyncio_logger.debug(
            f"Created Twitter Follower Monitor for User {self.twitter_user.name} (@{self.twitter_user.username})"
        )

    async def send_follower_alert(self, differences: set[tweepy.User]) -> None:
        # TODO Add buttons to the alert

        asyncio_logger.debug(f"Sending a tweet...")

        new_follows_str: str = ""
        for follow in differences:
            new_follows_str += f"• {follow.name} (@{follow.username})\n"

        if is_debugging():
            twitter_channel: discord.TextChannel = (
                await self.discord_client.fetch_channel(CHAN_BOT_SPAM_PRIVATE)
            )
        else:
            twitter_channel = await self.discord_client.fetch_channel(CHAN_TWITTERVERSE)

        embed: discord.Embed = buildEmbed(
            title="Twitter Follower Monitor",
            description=f"{str(self.twitter_user.name).title()}'s followers changed! Different Twitter followers below ",
            fields=[dict(name="", value="")],
        )

        await twitter_channel.send(embed=embed)

        asyncio_logger.info(f"Tweet sent!")

    async def check_differences(self) -> None:
        differences: Optional[set[tweepy.User]] = await self.get_differences()

        if differences:
            asyncio_logger.debug("Differences found")
            await self.send_follower_alert(differences=differences)
        else:
            asyncio_logger.debug("No differences found")

    async def get_differences(self) -> Optional[set[tweepy.User]]:
        asyncio_logger.debug("Attempting to check for Twitter Follower differences")

        # TODO Error handling could go here

        await self.twitter_user.compile(initial=False)

        if (
            self.twitter_user.new_followers
        ):  # TODO Does it matter if it's fewer followers?
            return set(self.twitter_user.orig_followers) ^ set(
                self.twitter_user.new_followers
            )
        else:
            return None

    def _threaded_func(self, func: Callable) -> None:
        self.thread = threading.Thread(target=func)
        self.thread.start()

    async def start(self) -> None:
        asyncio_logger.debug("Setting up Twitter Monitor Follower schedule")

        scheduler = AsyncIOScheduler()
        trigger = IntervalTrigger(hours=1)
        scheduler.add_job(self.check_differences, trigger=trigger)

        asyncio_logger.debug("Added a schedule job")

        while True:
            scheduler.start()
            await asyncio.sleep(1)


asyncio_logger.debug(f"{str(__name__).title()} module loaded!")
