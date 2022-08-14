import asyncio
import json
import logging
import os
import pathlib
import sys
from asyncio import Future
from typing import Union, Optional

import discord
import requests
import tweepy
from discord import HTTPException, NotFound, Forbidden
from tweepy import Response, StreamResponse, User

from helpers.constants import (
    CHAN_BOT_SPAM_PRIVATE,
    CHAN_FOOD,
    CHAN_GENERAL,
    CHAN_RECRUITING,
    CHAN_TWITTERVERSE,
    DEBUGGING_CODE,
    TWITTER_BLOCK16_SCREENANME,
    MEMBER_GEE,
)
from helpers.embed import buildEmbed, buildTweetEmbed

# logger = discordLogger(
#     name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
# )

tweepy_client: str = "tweepy.client"
level = logging.DEBUG
tweepy_client_logger: logging.Logger = logging.getLogger(tweepy_client)
tweepy_client_logger.setLevel(level=level)

tweepy_stream: str = "tweepy.streaming"
tweepy_stream_logger: logging.Logger = logging.getLogger(tweepy_stream)
tweepy_stream_logger.setLevel(level=level)

format_string: str = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
formatter: logging.Formatter = logging.Formatter(format_string)

filename: pathlib.Path = pathlib.Path(f"{tweepy_client}.log")
full_path: str = os.path.join(filename.parent.resolve(), "logs", filename)

file_handler: logging.FileHandler = logging.FileHandler(filename=full_path, mode="a")
file_handler.setFormatter(formatter)
file_handler.setLevel(level=level)

stream_handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(formatter)
stream_handler.setLevel(level=level)

tweepy_client_logger.addHandler(file_handler)
tweepy_client_logger.addHandler(stream_handler)

tweepy_stream_logger.addHandler(file_handler)
tweepy_stream_logger.addHandler(stream_handler)

logging.basicConfig(
    datefmt="%X %x",
    level=level,
    encoding="utf-8",
    handlers=[file_handler, stream_handler],
)

__all__: list[str] = ["StreamClientV2"]


# Example
# task = asyncio.run_coroutine_threadsafe(
#     send_tweet_alert(self.discord_client, "Connected!"), self.discord_client.loop
# )
# task.result()


async def send_errors(client: discord.Client, error):
    try:
        gee_member: discord.User = await client.fetch_user(MEMBER_GEE)
    except (NotFound, HTTPException):
        return

    error_message: str = ""

    if isinstance(error, requests.Response):
        _: requests.Response = error
        error_message = (
            "A Response was received from on_closed:\n"
            f"Content: {_.content}\n"
            f"Status Code: {_.status_code}\n"
            f"Reason: {_.reason}"
        )
    elif isinstance(error, Exception):
        _: Exception = error
        error_message = (
            f"An Exception was raised from on_exception:\n"
            f"Cause: {_.__cause__}\n"
            f"Context: {_.__context__}\n"
            f"Traceback:\n"
            f"```css\n"
            f"{_.__traceback__}"
            f"\n```"
        )
    elif isinstance(error, int):
        error_message = (
            "A status code was received from on_request_error:\n"
            f"Status Code: {error_message}"
        )
    elif isinstance(error, dict):
        _: dict = error
        error_message = (
            "An error was received from on_errors:\n"
            f"JSON Dumps:\n"
            f"```css\n"
            f"{json.dumps(_, indent=4, sort_keys=True)}"
            f"\n```"
        )
    else:
        error_message = "NONE"

    try:
        await gee_member.send(content=error_message)
    except (HTTPException, Forbidden, ValueError, TypeError):
        return


async def send_tweet_alert(client: discord.Client, message) -> None:
    if DEBUGGING_CODE:
        twitter_channel: discord.TextChannel = await client.fetch_channel(
            CHAN_BOT_SPAM_PRIVATE
        )
    else:
        twitter_channel = await client.fetch_channel(CHAN_TWITTERVERSE)

    tweepy_client_logger.debug(f"Tweet alert received: {message}")

    embed: discord.Embed = buildEmbed(
        title="Husker Twitter",
        fields=[
            dict(
                name="Twitter Stream Alert",
                value=str(message),
            )
        ],
    )

    await twitter_channel.send(embed=embed)

    tweepy_client_logger.info(f"Twitter alert sent!")


async def send_tweet(client: discord.Client, response: StreamResponse) -> None:
    class TwitterButtons(discord.ui.View):
        def __init__(
            self,
            timeout=1200,
        ) -> None:
            super(TwitterButtons, self).__init__()
            self.message: Optional[discord.Message] = None
            self.timeout = timeout
            self.client = client

        async def on_timeout(self) -> None:
            tweepy_client_logger.debug(
                "Twitter buttons have timed out. Removing all buttons"
            )

            self.clear_items()
            await self.message.edit(view=self)

        # noinspection PyMethodMayBeStatic
        def grabTwitterLink(self, message_embed: discord.Embed) -> str:
            link: list[str] = [
                field.value
                for field in message_embed.fields
                if field.name == "Link to Tweet"
            ]
            return "".join(link)

        @discord.ui.button(
            label="Send to General",
            custom_id="send_to_general",
            style=discord.ButtonStyle.gray,
        )
        async def send_to_general(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            tweepy_client_logger.debug("Sending tweet to general channel")

            general_channel = await client.fetch_channel(CHAN_GENERAL)

            await general_channel.send(
                f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
            )
            await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

        @discord.ui.button(
            label="Send to Recruiting",
            custom_id="send_to_recruiting",
            style=discord.ButtonStyle.gray,
        )
        async def send_to_recruiting(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            tweepy_client_logger.debug("Sending tweet to recruiting channel")

            recruiting_channel = await client.fetch_channel(CHAN_RECRUITING)

            await recruiting_channel.send(
                f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
            )
            await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

    tweepy_client_logger.debug(f"Sending a tweet...")

    if DEBUGGING_CODE:
        twitter_channel: discord.TextChannel = await client.fetch_channel(
            CHAN_BOT_SPAM_PRIVATE
        )
        food_channel: discord.TextChannel = await client.fetch_channel(
            CHAN_BOT_SPAM_PRIVATE
        )
    else:
        twitter_channel = await client.fetch_channel(CHAN_TWITTERVERSE)
        food_channel = await client.fetch_channel(CHAN_FOOD)

    embed = buildTweetEmbed(response=response)

    if response.includes["users"][0].name.lower() == TWITTER_BLOCK16_SCREENANME.lower():
        await food_channel.send(embed=embed)
    else:
        author: User = response.includes["users"][0]

        view: TwitterButtons = TwitterButtons()
        view.add_item(
            item=discord.ui.Button(
                style=discord.ButtonStyle.url,
                label="Open Tweet...",
                url=f"https://twitter.com/{author.username}/status/{response.data.id}",
            )
        )
        view.message = await twitter_channel.send(embed=embed, view=view)
        tweepy_client_logger.debug("Waiting for twitter buttons to be pushed")

        asyncio.run_coroutine_threadsafe(coro=view.wait(), loop=client.loop)

    tweepy_client_logger.info(f"Tweet sent!")


class StreamClientV2(tweepy.StreamingClient):
    __slots__ = [
        "bearer_token",
        "client",
    ]

    def __init__(
        self,
        bearer_token: str,
        discord_client: Optional[discord.Client],
        **kwargs,
    ) -> None:
        super().__init__(bearer_token, **kwargs)
        self.client = discord_client

    def remove_all_rules(self) -> None:
        raw_rules: Union[dict, Response, Response] = self.get_rules()
        if raw_rules.data is not None:
            ids: list[int] = [rule.id for rule in raw_rules.data]
            self.delete_rules(ids)

    def on_connect(self) -> None:
        raw_rules: Response = self.get_rules()
        auths: Union[str, list[str]] = ""

        if raw_rules.data is not None:
            for rule in raw_rules.data:
                auths += rule.value + " OR "

            auths = auths[:-4]
            auths = auths.replace("from:", "@")
            auths = auths.split(" OR ")
            auths = ", ".join(auths)

        tweepy_client_logger.info(f"Connected with the following rules: {auths}")

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_tweet_alert(
                client=self.client, message=f"Connected! Following: {auths}"
            ),
            loop=self.client.loop,
        )
        task.result()

    def on_response(self, response: StreamResponse):
        tweepy_client_logger.debug(
            f"Received a response with text ({response.data.text}) from Twitter Stream"
        )

        if "husker-media" not in [rule.tag for rule in response.matching_rules]:
            return

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_tweet(client=self.client, response=response),
            loop=self.client.loop,
        )
        task.result()

    def on_disconnect(self):
        tweepy_client_logger.debug("Twitter stream disconnected")

    def on_closed(self, response: requests.Response):
        tweepy_client_logger.debug(
            f"Twitter stream closed with {response.status_code} {response.text}"
        )

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_errors(client=self.client, error=response),
            loop=self.client.loop,
        )
        task.result()

    def on_exception(self, exception: Exception):
        tweepy_client_logger.debug(
            f"Twitter stream received an exception: {repr(exception)}"
        )

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_errors(client=self.client, error=exception),
            loop=self.client.loop,
        )
        task.result()

    def on_request_error(self, status_code: int):
        tweepy_client_logger.debug(
            f"Twitter stream received request erorr with {status_code}"
        )

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_errors(client=self.client, error=status_code),
            loop=self.client.loop,
        )
        task.result()

    def on_errors(self, errors: dict):
        for error in errors:
            tweepy_client_logger.debug(f"Twitter stream received the error {error}")

            task: Future = asyncio.run_coroutine_threadsafe(
                coro=send_errors(client=self.client, error=error),
                loop=self.client.loop,
            )
            task.result()


tweepy_client_logger.debug(f"{str(__name__).title()} module loaded!")
