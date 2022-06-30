from typing import Literal

import discord  # noqa # Beta version thing
from discord import HTTPException, NotFound, Forbidden
from discord.app_commands import CommandInvokeError, commands, MissingApplicationID
from discord.ext.commands import Context, Greedy

from objects.Client import HuskerClient
from objects.Logger import discordLogger

logger = discordLogger("__init__")

from helpers.constants import *  # noqa
from helpers.embed import *  # noqa
from helpers.encryption import *  # noqa
from helpers.fryer import *  # noqa
from helpers.misc import *  # noqa
from helpers.mysql import *  # noqa
from helpers.slowking import *  # noqa

from objects.Bets_Stats_Schedule import *  # noqa
from objects.Exceptions import *  # noqa
from objects.Paginator import *  # noqa
from objects.Recruits import *  # noqa
from objects.Survey import *  # noqa
from objects.Thread import *  # noqa
from objects.TweepyStreamListener import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

__all__ = ["client"]

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client = HuskerClient(
    command_prefix="$",
    fetch_offline_members=True,
    intents=intents,
    owner_id=MEMBER_GEE,
)

tree = client.tree


@tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: CommandInvokeError
) -> None:
    logger.info("app_command error detected!")

    try:
        await interaction.delete_original_message()
    except (HTTPException, NotFound, Forbidden):
        pass

    err = DiscordError(error, interaction.data.get("options", None))
    logger.error(error, exc_info=True)

    embed = buildEmbed(
        title="",
        fields=[
            dict(
                name=f"Error Type: {err.error_type}",
                value=f"{err.message}",
            ),
            dict(
                name="Command",
                value=f"{'/' + err.command if not err.parent else '/' + err.parent.name + ' ' + err.command}",
            ),
            dict(
                name="Command Input",
                value=f"{', '.join(err.options) if err.options else 'None'}",
            ),
            dict(name="Originating Module", value=f"{err.module}"),
        ],
    )

    # if interaction.response.is_done():
    if interaction.original_message() is not None:
        await interaction.followup.send(content="", embed=embed, ephemeral=True)
    else:
        # await interaction.channel.send(content="", embed=embed)
        await interaction.followup.send(content="", embed=embed, ephemeral=True)


@client.command()
@commands.guild_only()
async def sync(
    ctx: Context,
    guilds: Greedy[discord.Object],
    spec: Optional[Literal["~", "*", "^"]] = None,
) -> None:
    logger.info("Attempting to sync application commands")
    if not guilds:
        if spec == "~":  # Current guild
            logger.info("Syncing commands to current guild")
            synced = await client.tree.sync(guild=ctx.guild)
        elif spec == "*":  # Copies all global app commands to current guild and syncs
            logger.info("Copying all global application commands to current guild")
            client.tree.copy_global_to(guild=ctx.guild)
            synced = await client.tree.sync(guild=ctx.guild)
        elif (
            spec == "^"
        ):  # Clears all commands from the current guild target and syncs (removes guild commands)
            logger.info("Cleaering all application commands")
            client.tree.clear_commands(guild=ctx.guild)
            await client.tree.sync(guild=ctx.guild)
            synced = []
        else:
            logger.info("Syncing application commands")
            synced = await client.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            logger.info(f"Attempting to sync application commands to {guild}")
            await client.tree.sync(guild=guild)
        except Forbidden:
            logger.error(
                f"The guild {guild} does not have the ``applications.commands`` scope in the guild."
            )
        except MissingApplicationID:
            logger.error(f"The guild {guild} does not have an application ID.")
        except HTTPException:
            logger.error("Syncing the commands failed.")
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


discord_loggers = [
    "asyncio",
    "discord",
    "discord.client",
    "discord.gateway",
    "discord.http",
    "discord.state",
    "discord.webhook.async_",
]
for d_l in discord_loggers:
    _ = logging.getLogger(d_l)
    _.disabled = True

if DEBUGGING_CODE:
    logger.info("Attempting to connect to the test server")
    client.run(TEST_TOKEN, log_handler=None)
else:
    logger.info("Attempting to connect to the production server")
    client.run(PROD_TOKEN, log_handler=None)
