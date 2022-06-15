import asyncio
import json
import logging
import time
from pprint import pprint
from typing import Union

import dateutil.parser
import discord
import tweepy
from tweepy import Response

from helpers.constants import (
    CHAN_TWITTERVERSE,
    DEBUGGING_CODE,
    CHAN_GENERAL,
    CHAN_RECRUITING,
    CHAN_FOOD,
)
from helpers.embed import buildEmbed, buildTweetEmbed

logger = logging.getLogger(__name__)
handler = logging.FileHandler(filename="twitter_stream.log")
logger.addHandler(handler)

# Example
# task = asyncio.run_coroutine_threadsafe(
#     send_tweet_alert(self.client, "Connected!"), self.client.loop
# )
# task.result()


class MyTweet(object):
    def __init__(self, tweet_data) -> None:
        self.data = None
        self.includes = None
        self.matching_rules = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetMediaData(object):
    def __init__(self, tweet_data) -> None:
        self.url = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetQuoteData(object):
    def __init__(self, tweet_data) -> None:
        self.id = None
        self.text = None
        self.author_id = None
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetUserData(object):
    def __init__(self, data) -> None:
        self.public_metrics = None
        self.verified = None
        self.profile_image_url = None
        self.name = None
        self.username = None
        self.followers = None
        self.following = None
        self.tweet_count = None
        self.listed_count = None
        for key in data:
            setattr(self, key, data[key])


async def send_tweet_alert(client: discord.Client, message) -> None:
    if DEBUGGING_CODE:
        logger.info("Skipping tweet alert because debugging is on")
        return

    logger.info(f"Tweet alert received: {message}")
    embed = buildEmbed(
        title="Husker Twitter",
        fields=[
            dict(
                name="Twitter Stream Alert",
                value=str(message),
            )
        ],
    )

    twitter_channel: discord.TextChannel = await client.fetch_channel(CHAN_TWITTERVERSE)
    await twitter_channel.send(embed=embed)

    logger.info(f"Twitter alert sent!")


async def send_tweet(client: discord.Client, tweet: MyTweet) -> None:
    class TwitterButtons(discord.ui.View):
        def __init__(self):
            super().__init__()

        @discord.ui.button(
            label="Send to General",
            custom_id="send_to_general",
            style=discord.ButtonStyle.gray,
        )
        async def send_to_general(
            self, interaction: discord.Interaction, button: discord.ui.Button
        ):
            chan = await client.fetch_channel(CHAN_GENERAL)
            await chan.send(
                f"Tweet forwarded by {interaction.user.mention}",
                embed=interaction.message.embeds[0],
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
            chan = await client.fetch_channel(CHAN_RECRUITING)
            await chan.send(
                f"Tweet forwarded by {interaction.user.mention}",
                embed=interaction.message.embeds[0],
            )
            await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

        # NOTE Discord API preventing creating a URL button at this scope

    logger.info(f"Sending tweet")

    author = None  # noqa
    for user in tweet.includes["users"]:
        if tweet.data["author_id"] == user["id"]:
            author: TweetUserData = TweetUserData(user)
            break

    medias = []
    if "media" in tweet.includes:
        for item in tweet.includes["media"]:
            medias.append(TweetMediaData(item))

    quotes = []
    if "tweets" in tweet.includes:
        for item in tweet.includes["tweets"]:
            quotes.append(TweetQuoteData(item))

    if (
        author.username.lower() == "Block16Omaha".lower()
        and tweet.data.get("referenced_tweets", False)
        and tweet.data.get("in_reply_to_user_id", False)
    ):
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
            b16=True,
        )

        food_channel: discord.TextChannel = await client.fetch_channel(CHAN_FOOD)
        await food_channel.send(embed=embed)

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

    view = TwitterButtons()
    view.add_item(
        item=discord.ui.Button(
            style=discord.ButtonStyle.url,
            label="Open Tweet...",
            url=f"https://twitter.com/{author.username}/status/{tweet.data['id']}",
        )
    )
    twitter_channel: discord.TextChannel = await client.fetch_channel(CHAN_TWITTERVERSE)
    await twitter_channel.send(embed=embed, view=view)

    logger.info(f"Tweet sent!")


class StreamClientV2(tweepy.StreamingClient):
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
            ids = [rule.id for rule in raw_rules.data]
            self.delete_rules(ids)

    def on_connect(self) -> None:
        logger.info("Connected!")

        self.cooldown = 5

        raw_rules = self.get_rules()
        auths: Union[str, list[str]] = ""

        if raw_rules.data is not None:
            for rule in raw_rules.data:
                auths += rule.value + " OR "

            auths = auths[:-4]
            auths = auths.replace("from:", "@")
            auths = auths.split(" OR ")
            auths = ", ".join(auths)

        task = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, f"Connected! Following: {auths}"),
            self.client.loop,
        )
        task.result()

    def on_request_error(self, status_code) -> None:
        logger.exception(f"Request Error: {status_code}")
        # self.remove_all_rules()

        logger.info(
            f"Sleeping for {self.cooldown} seconds before attempting to reconnected"
        )
        time.sleep(self.cooldown)
        self.cooldown = min(self.cooldown * 2, 900)  # Max of 900 seconds or 15 minutes
        logger.info("Sleep is over")

    def on_connection_error(self) -> None:
        logger.exception(f"Connection Error")
        task = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(
                self.client, "The Twitter Stream had an error connecting!"
            ),
            self.client.loop,
        )
        task.result()
        # self.remove_all_rules()

    def on_disconnect(self) -> bool:
        logger.warning("Disconnected")
        task = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, "The Twitter Stream has been disconnected!"),
            self.client.loop,
        )
        task.result()
        # self.remove_all_rules()
        return True

    def on_errors(self, errors) -> None:
        logger.exception(f"Error received: {errors}")
        # self.remove_all_rules()

    def on_closed(self, response) -> None:
        logger.warning(f"Closed: {response}")
        # self.remove_all_rules()

    def on_exception(self, exception) -> None:
        logger.exception(f"Exception: {exception}")
        # self.remove_all_rules()

    def on_data(self, raw_data) -> None:
        logger.info(pprint(json.loads(raw_data)))

        processed_data = json.loads(raw_data)
        task = asyncio.run_coroutine_threadsafe(
            send_tweet(self.client, MyTweet(processed_data)), self.client.loop
        )
        task.result()

    def on_keep_alive(self):
        logger.info("Keep Alive signal received")
