import asyncio
import json
import logging

import discord
import tweepy

from helpers.constants import CHAN_TWITTERVERSE
from helpers.embed import buildEmbed
from objects.Exceptions import TwitterStreamException

logger = logging.getLogger(__name__)


# Example
# task = asyncio.run_coroutine_threadsafe(
#     send_tweet_alert(self.client, "Connected!"), self.client.loop
# )
# task.result()


class MyTweet(object):
    def __init__(self, tweet_data):
        self.data = None
        self.includes = None
        self.matching_rules = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetUserData(object):
    def __init__(self, data):
        self.verified = None
        self.profile_image_url = None
        self.name = None
        self.username = None
        for key in data:
            setattr(self, key, data[key])


async def send_tweet_alert(client: discord.Client, message):
    logger.info(f"Tweet alert received: {message}")
    embed = buildEmbed(
        title="Husker Twitter",
        fields=[
            dict(name="Twitter Stream Listener Alert", value=str(message), inline=False)
        ],
    )
    twitter_channel: discord.TextChannel = await client.fetch_channel(CHAN_TWITTERVERSE)
    await twitter_channel.send(embed=embed)
    logger.info(f"Twitter alert sent!")


async def send_tweet(client: discord.Client, tweet: MyTweet):
    logger.info(f"Sending tweet")

    # Embed title: display_name (@handle) via source
    # Field: name=Message, value=contents
    # Field: name=URL, value=URL
    # Footer: Tweet sent created_at
    author = None
    for user in tweet.includes["users"]:
        if tweet.data["author_id"] == user["id"]:
            author: TweetUserData = TweetUserData(user)
            break
    embed: discord.Embed = buildEmbed(
        title=f"{author.name} (@{author.username}{' ✅' if author.verified else ''}) via {tweet.data['source']}",
        fields=[
            dict(name="Message", value=tweet.data["text"], inline=False),
            dict(
                name="URL",
                value=f"https://twitter.com/{author.username}/status/{tweet.data['id']}",
                inline=False,
            ),
        ],
    )
    embed.set_footer(
        text=f"Tweet sent at {tweet.data['created_at']}",
    )
    embed.set_author(name=f"@{author.username}", icon_url=author.profile_image_url)

    logger.info(f"Tweet sent!")


class StreamClientV2(tweepy.StreamingClient):
    def __init__(
        self,
        bearer_token,
        client: discord.Client,
        **kwargs,
    ):
        super().__init__(bearer_token, **kwargs)
        self.client = client
        logger.info("StreamClientV2 Initialized")

    def on_connect(self):
        logger.info("Connected")
        debug = False
        if debug:
            task = asyncio.run_coroutine_threadsafe(
                send_tweet_alert(self.client, "Connected!"), self.client.loop
            )
            task.result()

    def on_disconnect(self):
        logger.info("Disconnected")
        task = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, "Disconnected!"), self.client.loop
        )
        task.result()

    def on_keep_alive(self):
        logger.info("Keep alive")

    def on_tweet(self, tweet):
        logger.info(f"Tweet received\n{tweet}")

    def on_errors(self, errors):
        logger.info(f"Error received\n{errors}")

    def on_closed(self, response):
        logger.info(f"Closed\n{response}")

    def on_exception(self, exception):
        logger.info(f"Exception\n{exception}")
        task = asyncio.run_coroutine_threadsafe(
            send_tweet_alert(self.client, "Exception received!"), self.client.loop
        )
        task.result()

    def on_includes(self, includes):
        logger.info(f"Includes\n{includes}")

    def on_response(self, response):
        logger.info(f"Response\n{response}")

    def on_data(self, raw_data):
        logger.info(f"Raw Data\n{raw_data}")
        processed_data = json.loads(raw_data)
        task = asyncio.run_coroutine_threadsafe(
            send_tweet(self.client, MyTweet(processed_data)), self.client.loop
        )
        task.result()

    def on_connection_error(self):
        logger.info(f"Connection Error")

    def on_matching_rules(self, matching_rules):
        logger.info(f"Matching Rules\n{matching_rules}")

    def on_request_error(self, status_code):
        logger.info(f"Request Error\n{status_code}")
