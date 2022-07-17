import asyncio
import json
import logging
import time
from asyncio import Future
from typing import Union, Optional

import dateutil.parser
import discord
import requests
import tweepy
from tweepy import Response

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
from objects.Exceptions import TwitterStreamException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = ["StreamClientV2"]


# Example
# task = asyncio.run_coroutine_threadsafe(
#     send_tweet_alert(self.client, "Connected!"), self.client.loop
# )
# task.result()


class MyTweet(object):
    __slots__ = [
        "data",
        "includes",
        "matching_rules",
    ]

    def __init__(self, tweet_data) -> None:
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetMediaData(object):
    __slots__ = [
        "alt_text",
        "duration_ms",
        "get",
        "height",
        "media_key",
        "preview_image_url",
        "public_metrics",
        "type",
        "url",
        "width",
    ]

    def __init__(self, tweet_data) -> None:
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetQuoteData(object):
    # __slots__ = [
    #     "attachments",
    #     "author_id",
    #     "context_annotations",
    #     "conversation_id",
    #     "created_at",
    #     "entities",
    #     "geo",
    #     "id",
    #     "in_reply_to_user_id",
    #     "lang",
    #     "possibly_sensitive",
    #     "public_metrics",
    #     "referenced_tweets",
    #     "reply_settings",
    #     "source",
    #     "text",
    #     "withheld",
    # ]

    def __init__(self, tweet_data) -> None:
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetUserData(object):
    __slots__ = [
        "created_at",
        "description",
        "entities",
        "following",
        "id",
        "listed_count",
        "location",
        "name",
        "pinned_tweet_id",
        "profile_image_url",
        "protected",
        "public_metrics",
        "tweet_count",
        "url",
        "username",
        "verified",
        "withheld",
    ]

    def __init__(self, tweet_data) -> None:
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


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


async def send_tweet(client: discord.Client, tweet: MyTweet) -> None:
    class TwitterButtons(discord.ui.View):
        __slots__ = [
            "children",
            "id",
            "message",
            "timeout",
        ]

        def __init__(self, timeout=1200) -> None:
            super(TwitterButtons, self).__init__()
            self.message: Optional[discord.Message, None] = None
            self.timeout = timeout

        # noinspection PyMethodMayBeStatic
        def grabTwitterLink(self, tweet_embed: discord.Embed) -> str:
            link: list[str] = [
                field.value
                for field in tweet_embed.fields
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
            chan: discord.TextChannel = await client.fetch_channel(CHAN_GENERAL)
            await chan.send(
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
            chan: discord.TextChannel = await client.fetch_channel(CHAN_RECRUITING)
            await chan.send(
                f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
            )
            await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

        async def on_timeout(self) -> None:
            logger.debug("Twitter buttons have timed out. Removing options")
            self.clear_items()
            await self.message.edit(view=self)

        async def callback(self, interaction: discord.Interaction) -> None:
            pass

    logger.debug(f"Sending a tweet")

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

    author: Optional[TweetUserData] = None
    for user in tweet.includes["users"]:
        if tweet.data["author_id"] == user["id"]:
            author = TweetUserData(user)
            break

    medias: list[TweetMediaData] = []
    if "media" in tweet.includes:
        for item in tweet.includes["media"]:
            medias.append(TweetMediaData(item))

    quotes: list[TweetQuoteData] = []
    if "tweets" in tweet.includes:
        for item in tweet.includes["tweets"]:
            quotes.append(TweetQuoteData(item))

    if author.username.lower() == TWITTER_BLOCK16_SCREENANME.lower():
        logger.info("Sending a Block 16 tweet")
        embed: discord.Embed = buildTweetEmbed(
            name=author.name,
            username=author.username,
            author_metrics=author.public_metrics,
            verified=author.verified,
            source=tweet.data["source"],
            text=tweet.data["text"],
            tweet_metrics=tweet.data["public_metrics"],
            tweet_id=tweet.data["id"],
            tweet_created_at=dateutil.parser.parse(tweet.data["created_at"]),
            profile_image_url=author.profile_image_url,
            urls=tweet.data["entities"],
            medias=medias,
            quotes=quotes,
            b16=True,
        )

        if food_channel:
            await food_channel.send(embed=embed)
        return

    embed = buildTweetEmbed(
        name=author.name,
        username=author.username,
        author_metrics=author.public_metrics,
        verified=author.verified,
        source=tweet.data["source"],
        text=tweet.data["text"],
        tweet_metrics=tweet.data["public_metrics"],
        tweet_id=tweet.data["id"],
        tweet_created_at=dateutil.parser.parse(tweet.data["created_at"]),
        profile_image_url=author.profile_image_url,
        urls=tweet.data["entities"],
        medias=medias,
        quotes=quotes,
    )

    view: TwitterButtons = TwitterButtons()
    view.add_item(
        item=discord.ui.Button(
            style=discord.ButtonStyle.url,
            label="Open Tweet...",
            url=f"https://twitter.com/{author.username}/status/{tweet.data['id']}",
        )
    )

    view.message = await twitter_channel.send(embed=embed, view=view)
    await view.wait()

    logger.info(f"Tweet sent!")


class StreamClientV2(tweepy.StreamingClient):
    __slots__ = ["client", "cooldown", "bearer_token"]

    def __init__(
        self,
        bearer_token,
        client: discord.Client,
        **kwargs,
    ) -> None:
        super().__init__(bearer_token, **kwargs)
        self.client = client
        self.cooldown = 5

    def remove_all_rules(self) -> None:
        raw_rules: Union[dict, Response, Response] = self.get_rules()
        if raw_rules.data is not None:
            ids: list[int] = [rule.id for rule in raw_rules.data]
            self.delete_rules(ids)

    def on_connect(self) -> None:
        logger.debug("Connected!")

        self.cooldown = 5

        raw_rules: Union[dict, Response, requests.Response] = self.get_rules()
        auths: Union[str, list[str]] = ""

        if raw_rules.data is not None:
            for rule in raw_rules.data:
                auths += rule.value + " OR "

            auths = auths[:-4]
            auths = auths.replace("from:", "@")
            auths = auths.split(" OR ")
            auths = ", ".join(auths)

        task: Future = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, f"Connected! Following: {auths}"),
            self.client.loop,
        )
        task.result()

    def on_request_error(self, status_code) -> None:
        logger.exception(f"Request Error: {status_code}")

        logger.debug(
            f"Sleeping for {self.cooldown} seconds before attempting to reconnected"
        )
        time.sleep(self.cooldown)
        self.cooldown = min(self.cooldown * 2, 900)  # Max of 900 seconds or 15 minutes
        logger.debug("Sleep is over")

    def on_connection_error(self) -> None:
        logger.exception(f"Connection Error")
        task: Future = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(
                self.client, "The Twitter Stream had an error connecting!"
            ),
            self.client.loop,
        )
        task.result()

    def on_disconnect(self) -> None:
        logger.warning("Disconnected")
        task: Future = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, "The Twitter Stream has been disconnected!"),
            self.client.loop,
        )
        task.result()

    def on_errors(self, errors) -> None:
        logger.exception(f"Error received: {errors}")

    def on_closed(self, response) -> None:
        logger.warning(f"Closed: {response}")

    def on_exception(self, exception: tweepy.HTTPException) -> None:
        # logger.exception(f"Exception: {exception}")
        raise TwitterStreamException(", ".join(exception.api_messages))

    def on_data(self, raw_data) -> None:
        processed_data: dict = json.loads(raw_data)
        task = asyncio.run_coroutine_threadsafe(
            send_tweet(self.client, MyTweet(processed_data)), self.client.loop
        )
        task.result()

    def on_keep_alive(self) -> None:
        logger.debug("Keep Alive signal received")


logger.debug(f"{str(__name__).title()} module loaded!")
