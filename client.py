# TODO
# * Bot status updates
# * Client events
# * Hall of Fame/Shame
# * Iowa checks
# * Reminders
# * Twitter stream
# TODO

import logging

import discord

from objects.Client import HuskerClient

__author__ = "u/refekt"
__version__ = "3.5.0b"

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

bot = HuskerClient(intents=intents)

__all__ = ["bot"]

# Get rid of spam
bot_loggers = ["gateway"]
for logger in bot_loggers:
    logging.getLogger(logger).handlers.clear()

# logger = logging.getLogger(f"{__name__}-frost")

reaction_threshold = 3  # Used for Hall of Fame/Shame

# server_stats = (
#     f"• __Onwer:__ {guild.owner_id}\n"
#     f"• __Description:__ {guild.description}\n"
#     f"• __Server Features:__ {features}\n"
#     f"• __Server Region:__ {guild.region}\n"
#     f"• __Vanity URL:__ {f'https://discord.gg/{guild.vanity_url_code}' if guild.vanity_url_code else 'N/A'}\n"
#     f"• __Boost Count:__ {guild.premium_subscription_count}\n"
#     f"• __Rules Channel:__ {getChannelMention(CHAN_ANNOUNCEMENT)}"
# )
