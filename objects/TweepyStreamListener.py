import ast
import asyncio
import json
import logging

import discord
import tweepy

from helpers.embed import buildEmbed

logger = logging.getLogger(__name__)


async def send_tweet_alert(channel: discord.TextChannel, message: str):
    logger.info(f"Twitter Alert: {message}")
    embed = buildEmbed(
        title="Husker Twitter",
        fields=[
            dict(name="Twitter Stream Listener Alert", value=message, inline=False)
        ],
    )
    await channel.send(embed=embed)


class StreamClientV2(tweepy.StreamingClient):
    def __init__(self, bearer_token, twitter_channel: discord.TextChannel, **kwargs):
        super().__init__(bearer_token, **kwargs)
        self.twitter_channel = twitter_channel
        logger.info("StreamClientV2 Initialized")

    def on_connect(self):
        logger.info("Connected")
        asyncio.run(send_tweet_alert(self.twitter_channel, "Twitter stream connected!"))

    def on_disconnect(self):
        logger.info("Disconnected")
        asyncio.run(
            send_tweet_alert(self.twitter_channel, "Twitter stream disconnected!")
        )

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

    def on_includes(self, includes):
        logger.info(f"Includes\n{includes}")

    def on_response(self, response):
        logger.info(f"Response\n{response}")

    def on_data(self, raw_data):
        logger.info(f"Raw Data\n{raw_data}")
        processed_data = json.loads(raw_data)

    def on_connection_error(self):
        logger.info(f"Connection Error")

    def on_matching_rules(self, matching_rules):
        logger.info(f"Matching Rules\n{matching_rules}")

    def on_request_error(self, status_code):
        logger.info(f"Request Error\n{status_code}")
