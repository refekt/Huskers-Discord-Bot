import asyncio
import typing

import tweepy
import discord
import threading
from utilities.constants import (
    TWITTER_BEARER,
    TWITTER_BOT_MEMBER,
    TWITTER_KEY,
    TWITTER_SECRET_KEY,
    TWITTER_TOKEN,
    TWITTER_TOKEN_SECRET
)
from utilities.constants import (
    pretty_time_delta,
    CHAN_TWITTERVERSE,
    TWITTER_HUSKER_MEDIA_LIST_ID
)
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlUpdateTasks
)

exitFlag = 0


class TwitterStreamListener(tweepy.StreamListener):
    def __init__(self, message_func, loop):
        super().__init__()
        self.message_func = message_func
        self.loop = loop

    def send_message(self, tweet):
        future = asyncio.run_coroutine_threadsafe(self.message_func(tweet), self.loop)
        future.result()

    def on_connect(self):
        print("### Twitter Stream Listening has connected.")

    def on_status(self, status):
        if not status.retweeted and status.in_reply_to_status_id is None:  # Check if Retweet
            self.send_message(status)

    def on_warning(self, notice):
        print(f"### ~~~ Twitter Stream Listener Error: {notice}")

    def on_timeout(self):
        print("### ~~~ Twitter Stream Listener timed out")

    def on_error(self, status_code):
        print(f"### ~~~ Twitter Stream Listener Error: {status_code}")

    def on_disconnect(self, notice):
        print(f"### Twitter Stream Listening has disconnected. Notice: {notice}")


async def send_reminder(num_seconds, destination: typing.Union[discord.Member, discord.TextChannel], message: str, source: typing.Union[discord.Member, discord.TextChannel], alert_when, missed=False):
    print(f"### ;;; Starting thread for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].")

    if not missed:
        print(f"### ;;; Destination: [{destination}]")
        print(f"### ;;; Message: [{message[:15] + '...'}]")

        await asyncio.sleep(num_seconds)

        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[
                ["Author", source.mention],
                [f"Reminder!", message]
            ]
        )
    else:
        embed = build_embed(
            title="Missed Bot Frost Reminder",
            inline=False,
            fields=[
                ["Original Reminder Date Time", alert_when],
                ["Author", source],
                ["Message", message]
            ]
        )
    await destination.send(embed=embed)

    Process_MySQL(sqlUpdateTasks, values=(0, str(destination.id), message, alert_when, str(source)))

    print(f"### ;;; Thread completed successfully!")
