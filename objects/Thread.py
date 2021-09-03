import asyncio
import typing

import discord
import tweepy

from utilities.constants import (
    pretty_time_delta
)
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlUpdateTasks
)

exitFlag = 0


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ {message}")


class TwitterStreamListener(tweepy.StreamListener):
    def __init__(self, message_func, loop):
        super().__init__()
        self.message_func = message_func
        self.loop = loop

    def send_message(self, tweet):
        future = asyncio.run_coroutine_threadsafe(self.message_func(tweet), self.loop)
        future.result()

    def on_connect(self):
        log(f"Twitter Stream Listening has connected.", 0)

    def on_status(self, status):
        # if not status.retweeted and status.in_reply_to_status_id is None and not hasattr(status, "retweeted_status"):
        self.send_message(status)

    def on_warning(self, notice):
        log(f"Twitter Stream Listener Error: {notice}", 1)

    def on_timeout(self):
        log(f"Twitter Stream Listener timed out", 1)

    def on_error(self, status_code):
        log(f"Twitter Stream Listener Error: {status_code}", 1)

    def on_disconnect(self, notice):
        log(f"Twitter Stream Listening has disconnected. Notice: {notice}", 1)


async def send_reminder(num_seconds, destination: typing.Union[discord.Member, discord.TextChannel], message: str, source: typing.Union[discord.Member, discord.TextChannel], alert_when, missed=False):
    log(f"Starting thread for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].", 1)

    if not missed:
        log(f"Destination: [{destination}]", 1)
        log(f"Message: [{message[:15] + '...'}]", 1)

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

    log(f";;; Thread completed successfully!")
