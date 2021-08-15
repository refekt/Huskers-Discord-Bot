import sys

import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand
from discord_slash.context import ComponentContext
from discord_slash.model import CallbackObject

from utilities.constants import TEST_TOKEN, PROD_TOKEN
from utilities.constants import production_server
from utilities.embed import build_embed

client = Bot(
    command_prefix="$",
    case_insensitive=True,
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
        f"### The bot is ready! ###"
    )


@client.event
async def on_slash_command_error(ctx, ex):
    embed = build_embed(
        title="Slash Command Error",
        fields=[
            ["Description", ex]
        ]
    )
    await ctx.send(embed=embed, hidden=True)


@client.event
async def on_component(ctx: ComponentContext):
    """ Called when a component is triggered. """
    pass


@client.event
async def on_component_callback(ctx: ComponentContext, callback: CallbackObject):
    pass


token = None

if len(sys.argv) > 0:
    if production_server():
        token = PROD_TOKEN
    else:
        token = TEST_TOKEN

extensions = [
    "commands.croot_bot",
    "commands.admin",
    "commands.text",
    "commands.image",
    "commands.football_stats",
    "commands.reminder",
    "commands.testing"
]
for extension in extensions:
    print(f"### ~~~ Loading extension: {extension} ###")
    client.load_extension(extension)

client.run(token)
