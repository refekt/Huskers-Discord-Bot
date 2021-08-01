import sys

import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from utilities.constants import \
    TEST_TOKEN, PROD_TOKEN
from utilities.server_detection import production_server

client = Bot(
    command_prefix="$",
    case_insensitive=True,
    help_command=None,
    description="Bot Frost version 3.0! Now with Slash Commands",
    intents=discord.Intents.all()
)

slash = SlashCommand(client, sync_commands=True)  # Sync required


@client.event
async def on_ready():
    print(
        f"### Bot Frost version 3.0 ###\n"
        f"### ~~~ Name: {client.user}\n"
        f"### ~~~ ID: {client.user.id}\n"
        f"### The bot is ready! ###\n"
    )


@client.event
async def on_connect():
    pass


@client.event
async def on_message(message):
    pass


@client.event
async def on_raw_reaction_add(payload):
    pass


@client.event
async def on_raw_reaction_remove(payload):
    pass


@client.event
async def on_member_join(member):
    pass


@client.event
async def on_error(event, *args, **kwargs):
    print(event, args, kwargs)


token = None

if len(sys.argv) > 0:
    if production_server():
        token = PROD_TOKEN
    else:
        token = TEST_TOKEN

# Load "cogs"?
client.load_extension("commands.croot_bot")

# client.run("ODcxMDc1NjAyNTgzNjU4NjA3.YQWCXw.KH34T89I1yzj7yeNoUgKRiJtXKc")
client.run(token)
