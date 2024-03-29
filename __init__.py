import asyncio
import datetime
import logging
import sys
import traceback
from typing import Literal, Optional

import discord
from discord import HTTPException, NotFound, Forbidden
from discord.app_commands import (
    AppCommand,
    CommandInvokeError,
    CommandTree,
    MissingApplicationID,
    commands,
)
from discord.ext.commands import Context, Greedy
from pymysql import IntegrityError, ProgrammingError

from objects.Logger import (
    discordLogger,
    initializeAsyncLogging,
    initializeLogging,
    is_debugging,
)

initializeLogging()
initializeAsyncLogging()

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

from helpers.constants import (
    CHAN_GENERAL,
    CHAN_NORTH_BOTTOMS,
    DT_TASK_FORMAT,
    FIELD_VALUE_LIMIT,
    MEMBER_GEE,
    PROD_TOKEN,
    ROLE_HYPE_MAX,
    ROLE_HYPE_NO,
    ROLE_HYPE_SOME,
    TZ,
)
from helpers.embed import buildEmbed
from helpers.mysql import processMySQL, sqlInsertWordle, sqlInsertXword
from objects import Wordle
from objects.Client import HuskerClient
from objects.Exceptions import DiscordError, WordleException, MySQLException
from objects.Wordle import WordleFinder
from objects.Xword import Xword

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

if "silent" not in sys.argv:

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

        if not isinstance(err.original.original, AssertionError):
            try:
                member_me: discord.Member = await interaction.guild.fetch_member(
                    MEMBER_GEE
                )
                await member_me.send(content=err.traceback)
            except (Forbidden, HTTPException, NotFound):
                pass
        else:
            logger.debug("Skipping DM for an error derived from Assert")

        if interaction.response.is_done():
            # Make error message hidden
            try:
                await interaction.delete_original_response()
                await interaction.followup.send(content="", embed=embed, ephemeral=True)
            except (HTTPException, NotFound, Forbidden):
                await interaction.channel.send(embed=embed)
        else:
            await interaction.followup.send(content="", embed=embed, ephemeral=True)

else:
    logger.debug("Skipping error output message in Discord")


@client.hybrid_command(name="manual-wordle")
@commands.default_permissions(administrator=True)
async def man_wordle(ctx: Context, who: discord.Member, *, wordle_input: str) -> None:
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
async def backlog_wordle(ctx: Context, year: int, month: int, day: int) -> None:
    north_bottoms: discord.TextChannel = ctx.guild.get_channel(CHAN_NORTH_BOTTOMS)
    general: discord.TextChannel = ctx.guild.get_channel(CHAN_GENERAL)
    wordle_finder: WordleFinder = WordleFinder()

    index: int = 0

    async for message in north_bottoms.history(
        oldest_first=True,
        after=datetime.datetime(year=year, month=month, day=day),
        limit=None,
    ):
        logger.debug(
            f"{message.created_at.astimezone(tz=TZ).strftime(DT_TASK_FORMAT)} {message.author.name}: {message.clean_content[:100]}"
        )

        index += 1

        if message.author.bot:
            continue

        try:
            wordle: Optional[Wordle] = wordle_finder.get_wordle_message(
                message=message, backup_finder=True
            )
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


@client.hybrid_command(name="backlog-nyxword")
@commands.default_permissions(administrator=True)
async def backlog_nyxword(ctx: Context, year: int, month: int, day: int) -> None:
    logger.debug("Starting backlog of New York cross word")
    north_bottoms: discord.TextChannel = ctx.guild.get_channel(CHAN_NORTH_BOTTOMS)

    index: int = 0

    async for message in north_bottoms.history(
        oldest_first=True,
        after=datetime.datetime(year=year, month=month, day=day),
        limit=None,
    ):
        index += 1

        if message.author.bot:
            continue

        nyxword: Optional[Xword] = Xword(message=message)

        if nyxword.url:
            logger.debug(
                f"New York crossword found! Message date: {message.created_at}"
            )

            author_id: str = str(message.author.id)

            try:
                processMySQL(
                    query=sqlInsertXword,
                    values=(
                        f"{author_id.rjust(5)}_{nyxword.xword_date}".strip(),
                        author_id,
                        nyxword.xword_date,
                        nyxword.seconds,
                        nyxword.url,
                    ),
                )
            except (MySQLException, IntegrityError, ProgrammingError) as e:
                logger.exception(f"MySQL encountered an error:\n{e}")
                continue


@client.hybrid_command(name="hype-audit")
@commands.default_permissions(administrator=True)
async def hype_audit(ctx: Context):
    logger.info("Beginning hype role audit")

    logger.debug("Generating list of hype roles")
    hype_roles: tuple[Optional[discord.Role], ...] = (
        ctx.guild.get_role(ROLE_HYPE_MAX),
        ctx.guild.get_role(ROLE_HYPE_SOME),
        ctx.guild.get_role(ROLE_HYPE_NO),
    )

    logger.debug("Generating list of hype members")
    hype_members: list[Optional[discord.Member]] = []

    for role in hype_roles:
        hype_members.extend(role.members)

    if not hype_members:
        logger.info("No hype members found")
        return

    logger.debug("Generating a list of hypers with more than hype role")
    seen: set = set()
    duplicate_hypers: list[Optional[discord.Member]] = [
        hyper for hyper in hype_members if hyper in seen or seen.add(hyper)
    ]

    hypers_str: str = ""
    hypers_list: list[Optional[str]] = []

    if duplicate_hypers:
        logger.debug("Removing hype roles from those with duplicate hypers")

        for hyper in duplicate_hypers:
            new_add: str = f"{hyper.mention}, "
            if len(hypers_str + new_add) > FIELD_VALUE_LIMIT:
                hypers_list.append(hypers_str)

            hypers_str += new_add

            try:
                await hyper.remove_roles(
                    *hype_roles, reason="/hype-audit - Clearing duplicate hype roles"
                )
            except (Forbidden, HTTPException):
                logger.debug(
                    f"Unable to clear {hyper.name}#{hyper.discriminator}'s roles"
                )
                continue

        if len(hypers_list) == 0:
            hypers_list.append(hypers_str)
    else:
        logger.info("No hypers with more than one role")

    if hypers_str:
        embed: discord.Embed = buildEmbed(
            title="Hyper Role Audit",
            fields=[
                dict(name="Audited Members", value=f"{item}") for item in hypers_list
            ],
        )
    else:
        embed = buildEmbed(
            title="Hyper Role Audit",
            description="No members found with duplicate roles.",
        )

    await ctx.send(embed=embed)


@client.hybrid_command(name="test")
@commands.default_permissions(administrator=True)
async def testing(ctx: Context):
    private_channel: discord.TextChannel = await client.fetch_channel(
        990262349703286864
    )

    if private_channel:
        async for message in private_channel.history(
            limit=20,
        ):
            if message.reactions:
                logger.debug([reaction.emoji.url for reaction in message.reactions])
            else:
                continue
    else:
        return


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


if is_debugging():
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
