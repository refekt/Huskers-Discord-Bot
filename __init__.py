import asyncio
import datetime
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
from pymysql import IntegrityError, ProgrammingError

from helpers.constants import MEMBER_GEE, PROD_TOKEN  # noqa
from helpers.embed import buildEmbed  # noqa
from objects import Wordle
from objects.Client import HuskerClient
from objects.Exceptions import DiscordError  # noqa
from objects.Logger import discordLogger
from objects.Wordle import WordleFinder

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG,  # if "Windows" in platform.platform() else logging.INFO,
)

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
from objects.Trivia import *  # noqa
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
            original=error,
            options=interaction.data.get("options", None),
            tb_msg=traceback.format_exc(),
        )

        logger.exception(error, exc_info=True)

        embed: discord.Embed = buildEmbed(
            title="",
            fields=[
                dict(
                    name=f"Error Type: {err.type}",
                    value=f"{err.message}",
                ),
                dict(name="Command", value=f"/{err.command}"),
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

else:
    logger.debug("Skipping error output message in Discord")


@client.hybrid_command(name="manual-wordle")
@commands.default_permissions(administrator=True)
async def man_wordle(ctx: Context, who: discord.Member, *, wordle_input: str):
    wordle_finder: WordleFinder = WordleFinder()

    try:
        wordle: Optional[Wordle] = wordle_finder.get_wordle_message(
            message=wordle_input
        )
    except (AssertionError, WordleException):
        return

    if wordle:
        logger.debug("Wordle found!")

        author: str = f"{who.name}#{who.discriminator}"

        try:
            processMySQL(
                query=sqlInsertWordle,
                values=(
                    f"{wordle.day}_{author}",
                    author,
                    wordle.day,
                    wordle.score,
                    wordle.green_squares,
                    wordle.yellow_squares,
                    wordle.black_squares,
                ),
            )

            logger.debug("Wordle MySQL processed")

        except (MySQLException, IntegrityError, ProgrammingError):
            return

        logger.debug(f"Manual Wordle input for {author} completed")


@client.hybrid_command(name="backlog-wordle")
@commands.default_permissions(administrator=True)
async def backlog(ctx: Context):
    north_bottoms: discord.TextChannel = ctx.guild.get_channel(CHAN_NORTH_BOTTOMS)
    general: discord.TextChannel = ctx.guild.get_channel(CHAN_GENERAL)
    wordle_finder: WordleFinder = WordleFinder()

    index: int = 0

    # async for message in north_bottoms.history(
    async for message in north_bottoms.history(
        # async for message in general.history(
        oldest_first=True,
        after=datetime.datetime(year=2022, month=1, day=14),
        limit=None,
    ):
        logger.debug(
            f"{message.created_at.astimezone(tz=TZ).strftime(DT_TASK_FORMAT)} {message.author.name}: {message.clean_content[:100]}"
        )

        index += 1

        if message.author.bot:
            continue

        try:
            wordle: Optional[Wordle] = wordle_finder.get_wordle_message(message=message)
        except (AssertionError, WordleException):
            continue

        if wordle:
            logger.debug("Wordle found!")

            author: str = f"{message.author.name}#{message.author.discriminator}"

            try:
                processMySQL(
                    query=sqlInsertWordle,
                    values=(
                        f"{wordle.day}_{author}",
                        author,
                        wordle.day,
                        wordle.score,
                        wordle.green_squares,
                        wordle.yellow_squares,
                        wordle.black_squares,
                    ),
                )

                logger.debug("Wordle MySQL processed")

            except (MySQLException, IntegrityError, ProgrammingError):
                continue


@client.command()
@commands.guild_only()
@commands.default_permissions(administrator=True)
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
            logger.info("Clearing all application commands")
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
    "discord.discord_client",
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
