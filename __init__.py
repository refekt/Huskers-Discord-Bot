import asyncio
import logging
import traceback
from typing import Literal, Optional

import discord  # noqa # Beta version thing
from discord import HTTPException, NotFound, Forbidden
from discord.app_commands import (
    CommandInvokeError,
    commands,
    MissingApplicationID,
    CommandTree,
    AppCommand,
)
from discord.ext.commands import Context, Greedy

from helpers.constants import MEMBER_GEE, PROD_TOKEN  # noqa
from helpers.embed import buildEmbed  # noqa
from objects.Client import HuskerClient  # , schedstop
from objects.Exceptions import DiscordError  # noqa
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
from objects.Timers import *  # noqa
from objects.TweepyStreamListener import *  # noqa
from objects.Weather import *  # noqa
from objects.Winsipedia import *  # noqa

__all__: list[str] = ["client"]

intents = discord.Intents.all()
intents.typing = False
intents.presences = False

client: HuskerClient = HuskerClient(
    command_prefix="$",
    fetch_offline_members=True,
    intents=intents,
    owner_id=MEMBER_GEE,
)

tree: CommandTree = client.tree

if not DEBUGGING_CODE:

    @tree.error
    async def on_app_command_error(
        interaction: discord.Interaction, error: CommandInvokeError
    ) -> None:
        logger.info("app_command error detected!")

        err: DiscordError = DiscordError(
            error, interaction.data.get("options", None), traceback.format_exc()
        )
        logger.exception(error, exc_info=True)

        embed: discord.Embed = buildEmbed(
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
        try:
            member_me: discord.Member = await interaction.guild.fetch_member(MEMBER_GEE)
            await member_me.send(content=err.traceback)
        except (Forbidden, HTTPException, NotFound):
            pass

        if interaction.response.is_done():
            # Make error message hidden
            try:
                await interaction.delete_original_message()
                await interaction.followup.send(content="", embed=embed, ephemeral=True)
            except (HTTPException, NotFound, Forbidden):
                await interaction.channel.send(embed=embed)
        else:
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
            synced: list[AppCommand] = await client.tree.sync(guild=ctx.guild)
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

    ret: int = 0
    for guild in guilds:
        try:
            logger.info(f"Attempting to sync application commands to {guild}")
            await client.tree.sync(guild=guild)
        except Forbidden:
            logger.exception(
                f"The guild {guild} does not have the ``applications.commands`` scope in the guild."
            )
        except MissingApplicationID:
            logger.exception(f"The guild {guild} does not have an application ID.")
        except HTTPException:
            logger.exception("Syncing the commands failed.")
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


discord_loggers: list[str] = [
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


async def main() -> None:
    async with client:
        await client.start(PROD_TOKEN)


try:
    asyncio.run(main())
except (KeyboardInterrupt, RuntimeError, SystemExit):
    pass

logger.info("Closing the bot")
