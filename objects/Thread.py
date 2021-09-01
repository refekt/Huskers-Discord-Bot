import asyncio
import typing

# import tweepy
import discord

# from utilities.constants import (
#     TWITTER_BEARER,
#     TWITTER_BOT_MEMBER,
#     TWITTER_KEY,
#     TWITTER_SECRET_KEY,
#     TWITTER_TOKEN,
#     TWITTER_TOKEN_SECRET
# )
from utilities.constants import pretty_time_delta
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlUpdateTasks
)

exitFlag = 0


def callback_function(func, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(func(args))
    loop.close()


async def send_reminder(num_seconds, destination: typing.Union[discord.Member, discord.TextChannel], message: str, source: typing.Union[discord.Member, discord.TextChannel], alert_when, missed=False):
    print(f"### ;;; Starting thread for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].")

    if not missed:
        print(f"### ;;; Creating a task for [{pretty_time_delta(num_seconds)}] seconds. [{destination}] [{message[:15] + '...'}]")
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
