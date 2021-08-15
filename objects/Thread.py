import asyncio
import threading
import typing
from datetime import datetime

import discord
from utilities.constants import DT_OBJ_FORMAT
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlUpdateTasks

exitFlag = 0


def remove_mentions(message):
    return str(message).replace("<", "[").replace("@!", "").replace(">", "]")


async def send_reminder(thread, num_seconds, destination: typing.Union[discord.Member, discord.TextChannel], message: str, source: typing.Union[discord.Member, discord.TextChannel], alert_when=None):
    if exitFlag:
        thread.exit()

    print(f"### ;;; Starting [{thread}] thread for [{num_seconds}] seconds. Send_When == [{alert_when}].")

    if num_seconds > 0:
        print(f"### ;;; Creating a task for [{num_seconds}] seconds. [{destination}] [{message[:15] + '...'}]")
        await asyncio.sleep(num_seconds)
        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[
                [f"Reminder!", remove_mentions(message)],
                ["Author", source.mention]
            ]
        )
    else:
        imported_datetime = datetime.strptime(alert_when, DT_OBJ_FORMAT)  # "%Y-%m-%d %H:%M:%S.%f")
        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[
                [f"Missed reminder from [{source.mention}] for [{destination.mention}]", remove_mentions(message)],
                ["Original Reminder Date Time", imported_datetime.strftime("%x %X")]
            ]
        )

    await destination.send(embed=embed)

    Process_MySQL(sqlUpdateTasks, values=(0, destination.id, message, alert_when, str(source)))

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
