import asyncio
import random
import threading
import typing
from datetime import datetime

import discord

from utils.mysql import process_MySQL, sqlUpdateTasks

exitFlag = 0


def remove_mentions(message):
    return str(message).replace("<", "[").replace("@!", "").replace(">", "]")


async def send_math(channel: discord.TextChannel):
    first = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    second = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

    await channel.send(f"Math time! What is {random.choice(first)} x {random.choice(second)}?")


class MathThread(threading.Thread):
    def __init__(self, event, channel: discord.TextChannel):
        threading.Thread.__init__(self)
        self.stopped = event
        self.channel = channel

    async def run(self):
        duration = 180
        while True:
            print("Sending math problem")
            await send_math(channel=self.channel)
            print(f"Sleeping {duration} seconds")
            await asyncio.sleep(duration)
            print("Slept!")


async def send_reminder(thread, duration, who: typing.Union[discord.Member, discord.TextChannel], message, author: typing.Union[discord.Member, discord.TextChannel], flag=None):
    if exitFlag:
        thread.exit()

    print(f"### ;;; Starting [{thread}] thread for [{duration}] seconds. Send_When == [{flag}].")

    if duration > 0:
        print(f"### ;;; Creating a task for [{duration}] seconds. [{who}] [{message[:15] + '...'}]")
        await asyncio.sleep(duration)
        await who.send(f"[Reminder from [{author}] for {who}]: {remove_mentions(message)}")
        process_MySQL(sqlUpdateTasks, values=(0, who.id, message, str(flag), author))
    else:
        imported_datetime = datetime.strptime(flag, "%Y-%m-%d %H:%M:%S.%f")
        await who.send(f"[Missed reminder from [{author}] for [{who}] set for [{imported_datetime.strftime('%x %X')}]!: {remove_mentions(message)}")
        process_MySQL(sqlUpdateTasks, values=(0, who.id, message, str(flag), author))

    print(f"### ;;; Thread [{thread}] completed successfully!")


class TaskThread(threading.Thread):
    def __init__(self, threadID, name, duration, who: typing.Union[discord.Member, discord.User], message: str, flag):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.duration = duration
        self.who = who
        self.message = message
        self.flag = flag

    async def run(self):
        await send_reminder(self.name, self.duration, self.who, self.message, self.flag)
