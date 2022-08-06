import asyncio
import logging
from asyncio import Future
from typing import Union, Optional

import discord
import tweepy
from tweepy import Response, StreamResponse, User

from helpers.constants import (
    CHAN_BOT_SPAM_PRIVATE,
    CHAN_FOOD,
    CHAN_GENERAL,
    CHAN_RECRUITING,
    CHAN_TWITTERVERSE,
    DEBUGGING_CODE,
    TWITTER_BLOCK16_SCREENANME,
)
from helpers.embed import buildEmbed, buildTweetEmbed
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = ["StreamClientV2"]


# Example
# task = asyncio.run_coroutine_threadsafe(
#     send_tweet_alert(self.discord_client, "Connected!"), self.discord_client.loop
# )
# task.result()


async def send_tweet_alert(client: discord.Client, message) -> None:
    if DEBUGGING_CODE:
        twitter_channel: discord.TextChannel = await client.fetch_channel(
            CHAN_BOT_SPAM_PRIVATE
        )
    else:
        twitter_channel = await client.fetch_channel(CHAN_TWITTERVERSE)

    logger.debug(f"Tweet alert received: {message}")

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

    logger.info(f"Twitter alert sent!")


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
            logger.debug("Twitter buttons have timed out. Removing all buttons")

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
            logger.debug("Sending tweet to general channel")

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
            logger.debug("Sending tweet to recruiting channel")

            recruiting_channel = await client.fetch_channel(CHAN_RECRUITING)

            await recruiting_channel.send(
                f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
            )
            await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

    logger.debug(f"Sending a tweet...")

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
        logger.debug("Waiting for twitter buttons to be pushed")

        asyncio.run_coroutine_threadsafe(coro=view.wait(), loop=client.loop)

    logger.info(f"Tweet sent!")


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

        logger.info(f"Connected with the following rules: {auths}")

        task: Future = asyncio.run_coroutine_threadsafe(
            coro=send_tweet_alert(
                client=self.client, message=f"Connected! Following: {auths}"
            ),
            loop=self.client.loop,
        )
        task.result()

    def on_response(self, response: StreamResponse):
        logger.debug(
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
        logger.debug("Twitter stream disconnected")

    def on_closed(self, response):
        logger.debug(
            f"Twitter stream closed with {response.status_code} {response.text}"
        )

    def on_exception(self, exception):
        logger.debug(f"Twitter stream received an exception: {repr(exception)}")

    def on_request_error(self, status_code):
        logger.debug(f"Twitter stream received request erorr with {status_code}")

    def on_errors(self, errors):
        for error in errors:
            logger.debug(f"Twitter stream received the error {error}")


logger.debug(f"{str(__name__).title()} module loaded!")
