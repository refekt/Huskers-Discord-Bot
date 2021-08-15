import asyncio
import threading
import typing
from datetime import datetime

import discord

from utilities.constants import DT_TASK_FORMAT
from utilities.constants import pretty_time_delta
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlUpdateTasks

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

    async def run(self):
        await send_reminder(
            thread_name=self.thread_name,
            num_seconds=self.num_seconds,
            destination=self.destination,
            message=self.message,
            source=self.source,
            flag=self.flag,
            alert_when=self.alert_when
        )
