# TODO
# * Modernize and revamp

import logging

logger = logging.getLogger(__name__)

# __all__ = [""]

logger.info(f"{str(__name__).title()} module loaded!")

# import asyncio
# import typing
#
# import discord
# import tweepy
# import time
#
# from helpers.constants import pretty_time_delta
# from helpers.embed import build_embed
# from helpers.mysql import Process_MySQL, sqlUpdateTasks
#
# exitFlag = 0
#
#
# def log(level: int, message: str):
#     import datetime
#
#     if level == 0:
#         print(f"[{datetime.datetime.now()}] ### Twitter Stream: {message}")
#     elif level == 1:
#         print(f"[{datetime.datetime.now()}] ### ~~~ Twitter Stream: {message}")
#
#
# async def send_reminder(
#     num_seconds,
#     destination: typing.Union[discord.Member, discord.TextChannel],
#     message: str,
#     source: typing.Union[discord.Member, discord.TextChannel],
#     alert_when,
#     missed=False,
# ):
#     log(
#         f"Starting thread for [{pretty_time_delta(num_seconds)}] seconds. Send_When == [{alert_when}].",
#         1,
#     )
#
#     if not missed:
#         log(1, f"Destination: [{destination}]")
#         log(1, f"Message: [{message[:15] + '...'}]")
#
#         await asyncio.sleep(num_seconds)
#
#         embed = build_embed(
#             title="Bot Frost Reminder",
#             ,
#             fields=[["Author", source.mention], [f"Reminder!", message]],
#         )
#     else:
#         embed = build_embed(
#             title="Missed Bot Frost Reminder",
#             ,
#             fields=[
#                 ["Original Reminder Date Time", alert_when],
#                 ["Author", source],
#                 ["Message", message],
#             ],
#         )
#     await destination.send(embed=embed)
#
#     Process_MySQL(
#         sqlUpdateTasks,
#         values=(0, str(destination.id), message, alert_when, str(source)),
#     )
#
#     log(0, f"Thread completed successfully!")
