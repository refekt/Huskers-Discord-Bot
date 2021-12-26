# TODO
# * Modernize and revamp
# TODO
import logging

logger = logging.getLogger(__name__)
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
# class TwitterStreamListener(tweepy.Stream):
#     def __init__(
#         self,
#         consumer_key,
#         consumer_secret,
#         access_token,
#         access_token_secret,
#         message_func,
#         alert_func,
#         loop,
#     ):
#         super().__init__(
#             consumer_key, consumer_secret, access_token, access_token_secret
#         )
#         self.consumer_key = consumer_key
#         self.consumer_secret = consumer_secret
#         self.access_token = access_token
#         self.access_token_secret = access_token_secret
#         self.message_func = message_func
#         self.alert_func = alert_func
#         self.loop = loop
#         self.cooldown = 1
#
#     def reset_cooldown(self):
#         self.cooldown = 0
#
#     def process_cooldown(self):
#         log(1, f"Pausing for {self.cooldown} seconds")
#         # asyncio.sleep(self.cooldown)
#         time.sleep(self.cooldown)
#         self.cooldown = min(self.cooldown * 2, 600)  # 10 minute max
#         log(1, f"Pause complete. New timer is {self.cooldown} seconds")
#
#     def send_message(self, tweet):
#         log(1, "Sending a new tweet")
#         future = asyncio.run_coroutine_threadsafe(self.message_func(tweet), self.loop)
#         future.result()
#
#     def send_alert(self, message):
#         log(1, "Sending an alert")
#         future = asyncio.run_coroutine_threadsafe(self.alert_func(message), self.loop)
#         future.result()
#
#     def on_connect(self):
#         log(0, f"Stream connected")
#         self.send_alert(f"Stream connected!")
#         self.reset_cooldown()
#
#     def on_status(self, status):
#         # if not status.retweeted and status.in_reply_to_status_id is None and not hasattr(status, "retweeted_status"):
#         log(1, f"Status received")
#         self.send_message(status)
#
#     def on_warning(self, notice):
#         log(1, f"Warning: {notice}")
#
#     def on_connection_error(self):
#         log(1, f"Connection error")
#         self.send_alert(f"Stream failed to connect.")
#         self.process_cooldown()
#         # return True  # Reconnect
#
#     def on_request_error(self, status_code):
#         log(1, f"Request Error: {status_code}")
#         if status_code == 420:
#             rl_msg = (
#                 f"Stream is being rate limited. Retrying in {self.cooldown} seconds..."
#             )
#             log(
#                 rl_msg,
#                 1,
#             )
#             self.send_alert(rl_msg)
#             self.process_cooldown()
#         else:
#             log(1, f"Request Error: {status_code}")
#             return True  # Reconnect
#
#     async def on_disconnect_message(self, message):
#         log(1, f"Stream disconnected. Notice: {message}")
#         self.send_alert(
#             f"Stream was disconnected. Retrying in {self.cooldown} seconds..."
#         )
#         self.process_cooldown()
#         self.send_alert("Stream attempting to reconnect!")
#
#         return True  # Reconnect
#
#     def on_keep_alive(self):
#         log(1, "Stream has received a keep alive signal.")
#         # self.process_cooldown()
#
#     def on_exception(self, exception):
#         log(1, f"Exception: {exception}")
#         self.process_cooldown()
#         return True
#
#     def on_limit(self, track):
#         log(
#             f"Stream is being rate limited. Unable to deliver {track} tweets",
#             1,
#         )
#         self.send_alert(
#             f"Stream is being rate limited. Unable to deliver {track} tweets"
#         )
#         self.process_cooldown()
#
#         # self.send_alert("Twitter stream attempting to reconnect!")
#         # return True  # Reconnect
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
#             inline=False,
#             fields=[["Author", source.mention], [f"Reminder!", message]],
#         )
#     else:
#         embed = build_embed(
#             title="Missed Bot Frost Reminder",
#             inline=False,
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
