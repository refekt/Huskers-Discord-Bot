import asyncio
import threading
import typing
import tweepy
import discord
from utilities.constants import TWITTER_BEARER, TWITTER_KEY, TWITTER_BOT_MEMBER, TWITTER_TOKEN, TWITTER_SECRET_KEY, TWITTER_TOKEN_SECRET
from utilities.constants import pretty_time_delta
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlUpdateTasks
from utilities.constants import CommandError
import json

exitFlag = 0


def remove_mentions(message):
    return str(message).replace("<", "[").replace("@!", "").replace(">", "]")


async def send_reminder(thread_name, num_seconds, destination: typing.Union[discord.Member, discord.TextChannel], message: str, source: typing.Union[discord.Member, discord.TextChannel], flag=False, alert_when=None):
    if flag:
        thread_name.exit()

    print(f"### ;;; Starting [{str(thread_name)}] thread_name for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].")

    if num_seconds > 0:
        print(f"### ;;; Creating a task for [{pretty_time_delta(num_seconds)}] seconds. [{destination}] [{message[:15] + '...'}]")
        await asyncio.sleep(num_seconds)
        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[
                [f"Reminder!", message],
                ["Author", source.mention]
            ]
        )
    else:
        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            destination="Missed reminder!",
            fields=[
                ["Destination", destination.mention],
                ["Message", message],
                ["Original Reminder Date Time", alert_when]
            ]
        )
    await destination.send(embed=embed)

    Process_MySQL(sqlUpdateTasks, values=(0, str(destination.id), message, alert_when, str(source)))

    print(f"### ;;; Thread [{str(thread_name)}] completed successfully!")


class TwitterStreamer(tweepy.StreamListener):
    def on_connect(self):
        print("### Twitter stream listener has started")

    def on_disconnect(self, notice):
        print(f"### Twitter stream listener has ended:\n{notice}")

    def on_data(self, raw_data):
        data = json.loads(raw_data)
        print(data)


async def start_twitter_stream():
    twitter_auth = tweepy.OAuthHandler(
        consumer_key=TWITTER_KEY,
        consumer_secret=TWITTER_SECRET_KEY
    )
    twitter_api = tweepy.API(twitter_auth)

    husker_list = twitter_api.get_list(
        list_id=1307680291285278720
    )
    husker_list_members = twitter_api.list_members(
        list_id=1307680291285278720
    )

    tweet_listener = TwitterStreamer()
    tweet_stream = tweepy.Stream(auth=twitter_api.auth, listener=tweet_listener)
    # tweet_stream.filter(+
    #     track=husker_list_members
    # )


class TaskThread(threading.Thread):
    def __init__(self, threadID, thread_name, num_seconds, destination: typing.Union[discord.Member, discord.User], message: str, source, flag, alert_when):
        threading.Thread.__init__(self)
        # self.threadID = threadID
        self.thread_name = thread_name
        self.num_seconds = num_seconds
        self.destination = destination
        self.message = message
        self.source = source
        self.flag = flag
        self.alert_when = alert_when

    async def run(self, which: str = "reminder"):
        if which == "reminder":
            await send_reminder(
                thread_name=self.thread_name,
                num_seconds=self.num_seconds,
                destination=self.destination,
                message=self.message,
                source=self.source,
                flag=self.flag,
                alert_when=self.alert_when
            )
        elif which == "twitter":
            await start_twitter_stream()
