import asyncio
import logging
import os
import pathlib
import sys
import tracemalloc
from datetime import timedelta
from os import listdir
from typing import Union, Any, Awaitable, Optional

import discord
import tweepy
from discord import NotFound, Forbidden, HTTPException
from discord.app_commands import MissingApplicationID
from discord.ext.commands import Bot, ExtensionAlreadyLoaded
from pymysql import IntegrityError, ProgrammingError
from tweepy import Response

from __version__ import _version
from commands.reminder import MissedReminder, send_reminder
from helpers.constants import (
    BOT_ICON_URL,
    CHAN_BOT_SPAM,
    CHAN_BOT_SPAM_PRIVATE,
    CHAN_GENERAL,
    CHAN_HOF,
    CHAN_HOS,
    CHAN_NORTH_BOTTOMS,
    DEBUGGING_CODE,
    GUILD_PROD,
    TWITTER_BEARER,
    TWITTER_BLOCK16_SCREENANME,
    TWITTER_EXPANSIONS,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_MEDIA_FIELDS,
    TWITTER_QUERY_MAX,
    TWITTER_TWEET_FIELDS,
    TWITTER_USER_FIELDS,
)
from helpers.embed import buildEmbed
from helpers.mysql import (
    SqlFetch,
    processMySQL,
    sqlGetWordleIndividualUserScore,
    sqlInsertWordle,
    sqlRetrieveReminders,
    sqlUpdateReminder,
)
from helpers.slowking import makeSlowking
from objects.Exceptions import ChangelogException, MySQLException
from objects.Logger import discordLogger
from objects.Scheudle import SchedulePosts
from objects.Thread import convert_duration
from objects.TweepyStreamListener import StreamClientV2
from objects.Wordle import WordleFinder, Wordle

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = [
    "GUILD_ROLES",
    "HuskerClient",
    "start_twitter_stream",
]

tracemalloc.start()

GUILD_ROLES: Optional[list[discord.Role]] = None


async def start_twitter_stream(client: discord.Client) -> None:
    logger.info("Bot is starting the Twitter stream")

    tweeter_stream = StreamClientV2(
        bearer_token=TWITTER_BEARER,
        discord_client=client,
        wait_on_rate_limit=True,
    )

    logger.debug("Twitter stream client created")

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()
    if raw_rules.data is not None:
        ids = [rule.id for rule in raw_rules.data]
        tweeter_stream.delete_rules(ids)

    logger.debug("Previous Twitter Stream rules deleted")

    tweeter_client = tweepy.Client(TWITTER_BEARER)
    list_members = tweeter_client.get_list_members(str(TWITTER_HUSKER_MEDIA_LIST_ID))

    logger.debug("Collected usernames from the Husker Media Twitter List")

    rule_query = ""
    rules: list[str] = []
    append_str: str = ""

    if DEBUGGING_CODE:
        rule_query = "from:ayy_gbr OR "

    rule_query += f"from:{TWITTER_BLOCK16_SCREENANME} OR "

    for member in list_members[0]:
        append_str = f"from:{member['username']} OR "

        if len(rule_query) + len(append_str) > TWITTER_QUERY_MAX:
            rule_query = rule_query[:-4]  # Get rid of ' OR '
            rules.append(rule_query)
            rule_query = ""

        rule_query += append_str

    rule_query = rule_query[:-4]  # Get rid of ' OR '
    rules.append(rule_query)

    del list_members, member, tweeter_client, append_str

    for stream_rule in rules:
        tweeter_stream.add_rules(tweepy.StreamRule(stream_rule, tag="husker-media"))

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()

    auths: Union[str, list[str]] = ""

    for rule in raw_rules.data:
        auths += rule.value + " OR "

    auths = auths[:-4]
    auths = auths.replace("from:", "@")
    auths = auths.split(" OR ")
    auths = ", ".join(auths)

    if raw_rules.data is not None:
        logger.debug(f"Twitter Stream rules: {auths}")
    else:
        logger.debug("No rules found")

    tweeter_stream.filter(
        expansions=TWITTER_EXPANSIONS,
        media_fields=TWITTER_MEDIA_FIELDS,
        tweet_fields=TWITTER_TWEET_FIELDS,
        user_fields=TWITTER_USER_FIELDS,
        threaded=True,
    )


class HuskerClient(Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.add_extensions = [
            "commands.admin",
            "commands.football_stats",
            "commands.image",
            "commands.recruiting",
            "commands.reminder",
            "commands.text",
        ]
        self.guild_user_len: int = 0
        self.reaction_threshold: int = 999
        self.wordle_finder: Optional[WordleFinder] = None

    async def check_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        if not payload.guild_id == GUILD_PROD or payload.channel_id in (
            CHAN_HOF,
            CHAN_HOS,
        ):  # Stay out of HOF and HOS
            logger.debug(
                "Reaction was either in HOF/HOS channel or not in the correct guild."
            )
            return None

        slowpoke_emoji: str = "<:slowpoke:758361250048245770>"
        reaction_channel: discord.TextChannel = await self.fetch_channel(
            payload.channel_id
        )
        reaction_message: discord.Message = await reaction_channel.fetch_message(
            payload.message_id
        )

        reactions_over_threshold: list[discord.Reaction] = [
            reaction
            for reaction in reaction_message.reactions
            if reaction.count >= self.reaction_threshold
        ]

        if not reactions_over_threshold:
            logger.debug(
                f"No reactions found over threshold found in {reaction_channel.name.encode('utf-8')}."
            )
            return None

        logger.info(
            f"Reaction threshold broken with [{reactions_over_threshold[0].count}] [{reactions_over_threshold[0].emoji.name}] reactions"
        )

        hof_channel: Optional[discord.TextChannel] = None
        hos_channel: Optional[discord.TextChannel] = None

        if str(reactions_over_threshold[0].emoji) == slowpoke_emoji:
            logger.debug("Hall of Shame threshold breached")
            hof: bool = False
            hos_channel: Optional[discord.TextChannel] = await self.fetch_channel(
                CHAN_HOS
            )
            raw_message_history: list[discord.Message] = [
                message async for message in hos_channel.history(limit=123)
            ]
        else:
            logger.debug("Hall of Fame threshold breached")
            hof = True
            hof_channel: Optional[discord.TextChannel] = await self.fetch_channel(
                CHAN_HOF
            )
            raw_message_history = [
                message async for message in hof_channel.history(limit=123)
            ]

        logger.debug("Checking for duplicate messages")
        duplicate: bool = False
        for raw_message in raw_message_history:
            if (
                len(raw_message.embeds) > 0
                and str(reaction_message.id) in raw_message.embeds[0].footer.text
            ):
                logger.debug("Duplicate message found. Exiting")
                duplicate = True
                break
        del raw_message_history

        file: Optional[discord.File] = None

        if not duplicate:
            if not hof:
                logger.debug("Creating Hall of Shame Embed")
                embed_title: str = (
                    f"{slowpoke_emoji * 3} Hall of Shame Message {slowpoke_emoji * 3}"
                )
                embed_description: str = (
                    "Messages so shameful they had to be memorialized forever!"
                )
                channel: discord.TextChannel = hos_channel

                file = makeSlowking(payload.member)
            else:
                logger.debug("Creating Hall of Fame Embed")
                embed_title = f"{'🏆' * 3} Hall of Fame Message {'🏆' * 3}"
                embed_description = (
                    "Messages so amazing they had to be memorialized forever!"
                )
                channel = hof_channel

            embed: discord.Embed = buildEmbed(
                title=embed_title,
                description=embed_description,
                file=file if file else None,
                fields=[
                    dict(name="Author", value=f"{reaction_message.author.mention}"),
                    dict(
                        name="Message",
                        value=f"{reaction_message.content}"
                        if reaction_message.content != ""
                        else f"{reaction_message.attachments[0].url}",
                    ),
                    dict(
                        name="Message Link",
                        value=f"[Click to view message]({reaction_message.jump_url})",
                    ),
                ],
                footer=f"Message ID: {reaction_message.id} | Hall of Shame message created at {reaction_message.created_at.strftime('%B %d, %Y at %H:%M%p')}",
            )
            await channel.send(embed=embed)

    # noinspection PyMethodMayBeStatic
    def get_change_log(self) -> [str, ChangelogException]:
        try:
            changelog_path = None
            changelog_file = "changelog.md"
            changelog_path = os.path.join(
                pathlib.Path(__file__).parent.parent.resolve(), changelog_file
            )
            changelog = open(changelog_path, "r")
            lines = changelog.readlines()
            lines_str = ""

            for line in lines:
                lines_str += str(line)

            return f"```\n{lines_str}```\n[Full GitHub Changelog](https://github.com/refekt/Bot-Frost/commits/master)"
        except OSError:
            logger.exception("Error loading the changelog!", exc_info=True)

    async def send_welcome_message(
        self, guild_member: Union[discord.Member, discord.User]
    ) -> None:
        channel_general: discord.TextChannel = await self.fetch_channel(CHAN_GENERAL)
        embed = buildEmbed(
            title="Hark! A new Husker fan emerges",
            description="Welcome the new member to the server!",
            fields=[
                dict(
                    name="New Member",
                    value=f"{guild_member.mention} ({guild_member.display_name}#{guild_member.discriminator})",
                ),
                dict(
                    name="Info",
                    value=f"Be sure to check out `/commands` for how to use the bot!",
                ),
            ],
            image=guild_member.avatar.url
            if guild_member.avatar.url is not ""
            else BOT_ICON_URL,
        )
        await channel_general.send(embed=embed)

    async def send_goodbye_message(
        self, guild_member: Union[discord.Member, discord.User]
    ):
        channel_general: discord.TextChannel = await self.fetch_channel(CHAN_GENERAL)

        embed = buildEmbed(
            title="Woe is us, {guild_member.display_name}#{guild_member.discriminator} fan departs",
            description="Say goodbye to another fair weather fan Mick ran off and Bart failed to ban",
            image=guild_member.avatar.url
            if guild_member.avatar.url is not ""
            else BOT_ICON_URL,
        )
        await channel_general.send(embed=embed)

    async def create_online_message(self) -> discord.Embed:
        return buildEmbed(
            title="Welcome to the Huskers server!",
            description="The official Husker football discord server",
            thumbnail="https://cdn.discordapp.com/icons/440632686185414677/a_061e9e57e43a5803e1d399c55f1ad1a4.gif",
            fields=[
                dict(
                    name="Support Bot Frost",
                    value="Check out `/donate` to see how you can support the project!",
                ),
                dict(
                    name="Commands",
                    value=f"View the list of commands with the `/commands` command. Note: Commands do not work in Direct Messages.",
                ),
                dict(
                    name="Version",
                    value=_version,
                ),
                dict(
                    name="Hall of Fame & Shame Reaction Threshold",
                    value=str(self.reaction_threshold),
                ),
                dict(
                    name="Changelog",
                    value=self.get_change_log(),
                ),
            ],
        )

    async def on_connect(self) -> None:
        logger.info("The bot has connected!")

        if len(self.guilds) > 1:
            logger.info(
                f"Bot is located in {len(self.guilds) - 1} other servers. Attempting to leave..."
            )
            for guild in self.guilds:
                if guild.id != GUILD_PROD:
                    try:
                        logger.info(f"Trying to leave {guild.name}")
                        await guild.leave()
                    except HTTPException:
                        logger.exception(f"Leaving guild {guild.name} failed")
        else:
            logger.info("Bot is only located in the Husker server")

    # noinspection PyMethodMayBeStatic
    async def on_ready(self) -> None:
        self.guild_user_len = len(self.users)
        self.reaction_threshold = int(0.0047 * self.guild_user_len)

        global GUILD_ROLES
        GUILD_ROLES = self.guilds[0].roles

        if DEBUGGING_CODE:
            chan_general: discord.TextChannel = await self.fetch_channel(
                CHAN_BOT_SPAM_PRIVATE
            )
            chan_botspam: discord.TextChannel = await self.fetch_channel(
                CHAN_BOT_SPAM_PRIVATE
            )
            chan_north_bottoms: discord.TextChannel = await self.fetch_channel(
                CHAN_BOT_SPAM_PRIVATE
            )
        else:
            chan_general = await self.fetch_channel(CHAN_GENERAL)
            chan_botspam = await self.fetch_channel(CHAN_BOT_SPAM)
            chan_north_bottoms = await self.fetch_channel(CHAN_NORTH_BOTTOMS)

        logger.info(
            f"Establishing Wordle Finder in {chan_north_bottoms.name.encode('utf-8')}"
        )
        self.wordle_finder = WordleFinder()

        logger.info(
            f"Reaction threshold for HOF and HOS messages set to [{self.reaction_threshold}]"
        )

        path = pathlib.Path(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/commands"
        ).resolve()  # Get path for /commands
        files = [
            f"commands.{file[:len(file) - 3]}"
            for file in listdir(path)
            if ".py" in str(file)
            and "testing" not in str(file)
            and "example" not in str(file)
        ]  # Get list of files that are not testing or example files and have .py extensions

        logger.info(f"Loading {len(files)} extensions")
        for extension in files:
            try:
                # NOTE Extensions will fail to load when runtime errors exist in the code.
                await self.load_extension(extension)
                logger.info(f"Loaded the [{extension}] extension")
            except ExtensionAlreadyLoaded:
                logger.info(f"The [{extension}] is already loaded. Skipping")
                continue
            except Exception as e:  # noqa
                logger.exception(f"Unable to load the {extension} extension\n{e}")
                continue

        logger.info("All extensions loaded")
        loaded_app_commands = None
        try:
            loaded_app_commands = await self.tree.sync(
                guild=discord.Object(id=GUILD_PROD)
            )
        except Forbidden:
            logger.exception(
                "The discord_client does not have the ``applications.commands`` scope in the guild."
            )
        except MissingApplicationID:
            logger.exception("The discord_client does not have an application ID.")
        except HTTPException:
            logger.exception("Syncing the commands failed.")

        logger.info(f"The bot tree has synced with {len(loaded_app_commands)} commands")

        on_ready_tasks: list[Awaitable] = []

        logger.info(f"Sys.argv is {sys.argv}")
        if "silent" in sys.argv:
            is_silent: bool = True
        else:
            is_silent = False
        logger.info(f"is_silent == {is_silent}")

        if is_silent:
            logger.info("Skipping Twitter stream")
        else:
            await start_twitter_stream(self)
            logger.info("Twitter stream started")

        if is_silent:
            logger.info("Skipping restarting reminders")
        else:
            logger.info("Collecting open reminders")
            open_reminders = processMySQL(
                query=sqlRetrieveReminders,
                fetch=SqlFetch.all,
                # fetch="all",
            )

            async def convertDestination(raw_send_to: str) -> discord.TextChannel:
                logger.debug("Attempting to fetch destination")
                try:
                    dest: Union[discord.TextChannel, None] = await self.fetch_channel(
                        int(raw_send_to)
                    )
                except NotFound:
                    dest = await self.fetch_channel(CHAN_BOT_SPAM)
                    pass

                logger.debug(f"destination is {dest.name.encode('utf-8')}")
                return dest

            async def convertSentTo(raw_send_to: str) -> Union[discord.User, None]:
                logger.debug("Attempting to fetch remind_who")
                try:
                    send_to: Union[discord.User, None] = await self.fetch_user(
                        int(raw_send_to)
                    )
                    logger.debug(
                        f"remind_who is {send_to.name.encode('utf-8')}#{send_to.discriminator}"
                    )
                except NotFound:
                    send_to = None
                    logger.debug("remind_who is None")
                    pass

                return send_to

            if open_reminders:
                logger.info(f"There are {len(open_reminders)} to be loaded")
                for index, reminder in enumerate(open_reminders):
                    destination = await convertDestination(reminder["send_to"])
                    remind_who = await convertSentTo(reminder["send_to"])
                    duration = convert_duration(reminder["send_when"])

                    logger.info(
                        f"Processing reminder #{index + 1}. Destination = {destination}, remind_who = {remind_who}, Message = {reminder['message'][:128]}"
                    )

                    if duration == timedelta(seconds=0):
                        logger.info(
                            f"Reminder exceeded original send datetime. Sending now!"
                        )

                        if destination == remind_who:
                            logger.exception(
                                "destination and remind_who are both None. Skipping!"
                            )
                            continue

                        await send_reminder(
                            author=reminder["author"],
                            destination=destination,
                            message=reminder["message"],
                            remind_who=remind_who,
                        )

                        processMySQL(
                            query=sqlUpdateReminder,
                            values=(
                                0,  # False
                                reminder["send_to"],
                                reminder["message"],
                                reminder["author"],
                            ),
                        )

                        del reminder  # Get rid of for accounting purposes
                    else:
                        logger.debug(
                            f"Adding reminder for/to [{reminder['send_to']}] to task list."
                        )

                        on_ready_tasks.append(
                            MissedReminder(
                                duration=duration,
                                author=reminder["author"],
                                destination=destination,
                                message=reminder["message"],
                                remind_who=remind_who,
                                missed_reminder=True,
                            ).run()
                        )
                logger.info("Compiled all open tasks")
            else:
                logger.info("No open reminders found")

        if is_silent:
            logger.info("Skipping daily posts schedule")
        else:
            logger.info("Creating daily posts schedule")
            scheduled_posts: SchedulePosts = SchedulePosts(channel=chan_general)
            scheduled_posts.setup_and_run_schedule()

            logger.info("Running scheduled_posts")
            self.loop.create_task(scheduled_posts.run())

        logger.info("Creating online message")
        await chan_botspam.send(embed=await self.create_online_message())

        if on_ready_tasks:
            logger.info(f"Processing {len(on_ready_tasks)} collected tasks")

            asyncio_logger = discordLogger(
                name="asyncio", level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
            )

            results: tuple[Union[BaseException, Any], ...] = await asyncio.gather(
                *on_ready_tasks, return_exceptions=True
            )

            for exc in [r for r in results if isinstance(r, BaseException)]:
                asyncio_logger.exception(
                    "Exception caught from on_ready_tasks_", exc_info=exc
                )

        logger.info("Finished on_ready_tasks stuff")

    async def on_member_join(self, guild_member: discord.Member) -> None:
        if guild_member.guild.id != GUILD_PROD:
            logger.info("Skipping on_member_join because not Husker server")
            return
        await self.send_welcome_message(guild_member)

    async def on_member_remove(self, guild_member: discord.Member) -> None:
        if guild_member.guild.id != GUILD_PROD:
            logger.info("Skipping on_member_join because not Husker server")
            return
        await self.send_goodbye_message(guild_member)

    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        logger.debug(f"Checking to see if reaction broke threshold")
        await self.check_reaction(payload)

    async def on_message(self, message: discord.Message) -> None:
        await self.process_commands(message)

        if message.author.bot or message.channel.id not in (
            CHAN_NORTH_BOTTOMS,
            CHAN_BOT_SPAM_PRIVATE,
        ):
            return

        if "Marty" in message.author.name:
            return

        wordle: Optional[Wordle] = self.wordle_finder.get_wordle_message(
            message=message
        )

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
                return

            author_score_str: Optional[str] = None

            try:  # The entire leaderboard required for MySQL's RANK() to work right
                leaderboard_scores: list[dict[str, Any]] = processMySQL(
                    query=sqlGetWordleIndividualUserScore,
                    fetch=SqlFetch.all,
                )

                author_score = [
                    score for score in leaderboard_scores if author in score.values()
                ]
                if len(author_score):
                    author_score = author_score[0]
                    author_score_str = f"They are the #{author_score['lb_rank']} Wordler with an average score of {author_score['score_avg']:0.1f}/6 over {author_score['games_played']} games"

                    logger.debug("Author scores retrieved")
                else:
                    logger.debug("No author scores retrieved")
            except (MySQLException, IntegrityError, ProgrammingError):
                logger.debug("Error getting leaderboard or author_scores")
                pass

            if wordle.score == wordle.failed_score:
                wordle_score_str: str = "X"
            else:
                wordle_score_str = wordle.score

            if author_score_str is None:
                embed = buildEmbed(
                    title="",
                    fields=[
                        dict(
                            name="Wordle Scored!",
                            value=f"{message.author.mention} submitted a Wordle score of {wordle_score_str}.",
                        ),
                    ],
                )
            else:
                embed = buildEmbed(
                    title="",
                    fields=[
                        dict(
                            name="Wordle Scored!",
                            value=f"{message.author.mention} submitted a Wordle score of {wordle_score_str}. {author_score_str}.",
                        ),
                    ],
                )

            await message.channel.send(embed=embed)


logger.info(f"{str(__name__).title()} module loaded!")
