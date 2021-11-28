import asyncio
import typing

import discord
import tweepy

from utilities.constants import pretty_time_delta
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlUpdateTasks

exitFlag = 0


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Twitter Stream: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Twitter Stream: {message}")


class TwitterStreamListener(tweepy.Stream):
    def __init__(
        self,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
        message_func,
        alert_func,
        loop,
    ):
        super().__init__(
            consumer_key, consumer_secret, access_token, access_token_secret
        )
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.message_func = message_func
        self.alert_func = alert_func
        self.loop = loop
        self.cooldown = 1

    def reset_cooldown(self):
        self.cooldown = 0

    def process_cooldown(self):
        log(f"Pausing for {self.cooldown} seconds", 1)
        asyncio.sleep(self.cooldown)
        self.cooldown *= 2
        log(f"Pause complete. New timer is {self.cooldown} seconds.", 1)

    def send_message(self, tweet):
        log("Sending a new tweet", 1)
        future = asyncio.run_coroutine_threadsafe(self.message_func(tweet), self.loop)
        future.result()

    def send_alert(self, message):
        log("Sending an alert", 1)
        future = asyncio.run_coroutine_threadsafe(self.alert_func(message), self.loop)
        future.result()

    def on_connect(self):
        log(f"Twitter Stream Listening has connected.", 0)

    def on_keep_alive(self):
        log("Keep alive message received", 1)

    def on_status(self, status):
        # if not status.retweeted and status.in_reply_to_status_id is None and not hasattr(status, "retweeted_status"):
        self.send_message(status)

    def on_warning(self, notice):
        log(f"Twitter Stream Listener Error: {notice}", 1)

    def on_connection_error(self):
        log(f"Twitter Stream Listener timed out", 1)
        self.process_cooldown()
        return True

    def on_request_error(self, status_code):
        log(f"Twitter Stream Listener Error: {status_code}", 1)
        if status_code == 420:
            self.process_cooldown()
            self.send_alert(f"Twitter Stream Listener Error: {status_code}")
            return True  # Reconnect

    def on_disconnect_message(self, message):
        log(f"Twitter Stream Listening has disconnected. Notice: {message}", 1)
        self.process_cooldown()
        return True

    def keep_alive(self):
        log("Twitter Stream Listener has received a keep alive signal.", 1)
        self.process_cooldown()
        return True

    def on_exception(self, exception):
        log(f"Twitter Stream Listener Error: {exception}", 1)
        self.process_cooldown()
        return True

    def on_limit(self, track):
        ...


async def send_reminder(
    num_seconds,
    destination: typing.Union[discord.Member, discord.TextChannel],
    message: str,
    source: typing.Union[discord.Member, discord.TextChannel],
    alert_when,
    missed=False,
):
    log(
        f"Starting thread for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].",
        1,
    )

    if not missed:
        log(f"Destination: [{destination}]", 1)
        log(f"Message: [{message[:15] + '...'}]", 1)

        await asyncio.sleep(num_seconds)

        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[["Author", source.mention], [f"Reminder!", message]],
        )
    else:
        embed = build_embed(
            title="Missed Bot Frost Reminder",
            inline=False,
            fields=[
                ["Original Reminder Date Time", alert_when],
                ["Author", source],
                ["Message", message],
            ],
        )
    await destination.send(embed=embed)

    Process_MySQL(
        sqlUpdateTasks,
        values=(0, str(destination.id), message, alert_when, str(source)),
    )

    log(f"Thread completed successfully!", 0)
