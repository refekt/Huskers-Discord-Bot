import asyncio
import threading
import typing
from datetime import datetime

import discord

from utilities.mysql import Process_MySQL, sqlUpdateTasks

exitFlag = 0


def remove_mentions(message):
    return str(message).replace("<", "[").replace("@!", "").replace(">", "]")


async def send_reminder(thread, duration, who: typing.Union[discord.Member, discord.TextChannel], message, author: typing.Union[discord.Member, discord.TextChannel], alert_when=None):
    if exitFlag:
        thread.exit()

    print(f"### ;;; Starting [{thread}] thread for [{duration}] seconds. Send_When == [{alert_when}].")

    if duration > 0:
        print(f"### ;;; Creating a task for [{duration}] seconds. [{who}] [{message[:15] + '...'}]")
        await asyncio.sleep(duration)
        await who.send(f"[Reminder from [{author}] for {who}]: {remove_mentions(message)}")
        Process_MySQL(sqlUpdateTasks, values=(0, who.id, message, alert_when, str(author)))
    else:
        imported_datetime = datetime.strptime(alert_when, "%Y-%m-%d %H:%M:%S.%f")
        await who.send(f"[Missed reminder from [{author}] for [{who}] set for [{imported_datetime.strftime('%x %X')}]!: {remove_mentions(message)}")
        Process_MySQL(sqlUpdateTasks, values=(0, who.id, message, alert_when, str(author)))

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
