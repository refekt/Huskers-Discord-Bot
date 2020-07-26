import asyncio
import threading
import typing
from datetime import datetime

import discord

from utils.mysql import process_MySQL, sqlUpdateTasks

exitFlag = 0


def remove_mentions(message):
    return str(message).replace("<", "[User: ").replace("@!", "").replace(">", "]")


class TaskThread(threading.Thread):
    def __init__(self, threadID, name, duration, who: typing.Union[discord.Member, discord.User], message: str, flag):
        # super().__init__(name)
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.duration = duration
        self.who = who
        self.message = message
        self.flag = flag

    async def run(self):
        await send_message(self.name, self.duration, self.who, self.message, self.flag)


async def send_message(thread, duration, who: typing.Union[discord.Member, discord.TextChannel], message, author: typing.Union[discord.Member, discord.TextChannel], flag=None):
    if exitFlag:
        thread.exit()

    print(f"### ;;; Starting [{thread}] thread for [{duration}] seconds. Send_When == [{flag}].")

    if duration > 0:
        print(f"### ;;; Creating a task for [{duration}] seconds. [{who}] [{message[:15] + '...'}]")
        await asyncio.sleep(duration)
        await who.send(f"[Reminder from [{author}] for {who.mention}]: {remove_mentions(message)}")
        process_MySQL(sqlUpdateTasks, values=(0, who.id, message, str(flag), author))
    else:
        imported_datetime = datetime.strptime(flag, "%Y-%m-%d %H:%M:%S.%f")
        await who.send(f"[Missed reminder from [{author}] for [{who.mention}] set for [{imported_datetime.strftime('%x %X')}]!: {remove_mentions(message)}")
        process_MySQL(sqlUpdateTasks, values=(0, who.id, message, str(flag), author))

    print(f"### ;;; Thread [{thread}] completed successfully!")
