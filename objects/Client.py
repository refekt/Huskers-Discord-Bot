import asyncio
import collections
import pathlib
import platform
from datetime import timedelta
from os import listdir
from typing import Union

import discord
import tweepy
from discord import NotFound
from discord.ext.commands import (
    Bot,
)
from tweepy import Response

from __version__ import _version
from commands.reminder import send_reminder, MissedReminder
from helpers.constants import (
    CHAN_BOT_SPAM,
    CHAN_GENERAL,
    CHAN_HOF,
    CHAN_HOS,
    DEBUGGING_CODE,
    DISCORD_CHANNEL_TYPES,
    GUILD_PROD,
    TWITTER_BEARER,
    TWITTER_BLOCK16_SCREENANME,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_QUERY_MAX,
)
from helpers.embed import buildEmbed
from helpers.mysql import processMySQL, sqlRetrieveReminders, sqlUpdateReminder
from helpers.slowking import makeSlowking
from objects.Exceptions import ChangelogException
from objects.Logger import discordLogger
from objects.Thread import convert_duration
from objects.TweepyStreamListener import StreamClientV2

logger = discordLogger(__name__)

__all__ = ["HuskerClient", "start_twitter_stream"]

logger.info(f"{str(__name__).title()} module loaded!")


def start_twitter_stream(client: discord.Client) -> None:
    logger.info("Bot is starting the Twitter stream")

    logger.info("Creating a stream client")
    tweeter_stream = StreamClientV2(
        bearer_token=TWITTER_BEARER,
        client=client,
        wait_on_rate_limit=True,
        # max_retries=5,
    )

    logger.info("Looking for any lingering stream rules")
    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()
    if raw_rules.data is not None:
        ids = [rule.id for rule in raw_rules.data]
        logger.info(f"Deleting rule ids: {' '.join(ids)}")
        tweeter_stream.delete_rules(ids)

    logger.info("Collecting Husker Media Twitter list")
    tweeter_client = tweepy.Client(TWITTER_BEARER)
    list_members = tweeter_client.get_list_members(TWITTER_HUSKER_MEDIA_LIST_ID)

    logger.info("Creating stream rule")
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
        logger.debug(f"Adding stream rule: {stream_rule}")
        tweeter_stream.add_rules(tweepy.StreamRule(stream_rule))

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()

    auths: Union[str, list[str]] = ""

    for rule in raw_rules.data:
        auths += rule.value + " OR "

    auths = auths[:-4]
    auths = auths.replace("from:", "@")
    auths = auths.split(" OR ")
    auths = ", ".join(auths)

    if raw_rules.data is not None:
        logger.info(f"Number of rules: {len(raw_rules.data)}")
    else:
        logger.info("No rules found")

    tweeter_stream.filter(
        expansions=[
            "attachments.media_keys",
            "attachments.poll_ids",
            "author_id",
            "entities.mentions.username",
            "geo.place_id",
            "in_reply_to_user_id",
            "referenced_tweets.id",
            "referenced_tweets.id.author_id",
        ],
        media_fields=[
            "alt_text",
            "duration_ms",
            "height",
            "media_key",
            "preview_image_url",
            "public_metrics",
            "type",
            "url",
            "width",
        ],
        place_fields=[
            "contained_within",
            "country",
            "country_code",
            "full_name",
            "geo",
            "id",
            "name",
            "place_type",
        ],
        poll_fields=[
            "duration_minutes",
            "end_datetime",
            "id",
            "options",
            "voting_status",
        ],
        tweet_fields=[
            "attachments",
            "author_id",
            "context_annotations",
            "conversation_id",
            "created_at",
            "entities",
            "geo",
            "id",
            "in_reply_to_user_id",
            "lang",
            "possibly_sensitive",
            "public_metrics",
            "referenced_tweets",
            "reply_settings",
            "source",
            "text",
            "withheld",
        ],
        user_fields=[
            "created_at",
            "description",
            "entities",
            "id",
            "location",
            "name",
            "pinned_tweet_id",
            "profile_image_url",
            "protected",
            "public_metrics",
            "url",
            "username",
            "verified",
            "withheld",
        ],
        threaded=True,
    )
    logger.info(f"Twitter stream is running: {tweeter_stream.running}")


class HuskerClient(Bot):
    add_extensions = [
        "commands.admin",
        "commands.football_stats",
        "commands.image",
        "commands.recruiting",
        "commands.reminder",
        "commands.text",
    ]
    guild_user_len: int = 0
    reaction_threshold: int = 0

    async def check_reaction(self, payload: discord.RawReactionActionEvent) -> None:
        if not payload.guild_id == GUILD_PROD or payload.channel_id in (
            CHAN_HOF,
            CHAN_HOS,
        ):  # Stay out of HOF and HOS
            return None

        slowpoke_emoji = "<:slowpoke:758361250048245770>"
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
                f"No reactions found over threshold found in {reaction_channel}."
            )
            return None

        logger.info(
            f"Reaction threshold broken with [{reactions_over_threshold[0].count}] [{reactions_over_threshold[0].emoji}] reactions"
        )
        hof_channel = hos_channel = None
        if str(reactions_over_threshold[0].emoji) == slowpoke_emoji:
            logger.info("Hall of Shame threshold breached")
            hof = False
            hos_channel: Union[discord.TextChannel, None] = await self.fetch_channel(
                CHAN_HOS
            )
            raw_message_history: list[discord.Message] = [
                message async for message in hos_channel.history(limit=123)
            ]
        else:
            logger.info("Hall of Fame threshold breached")
            hof = True
            hof_channel: Union[discord.TextChannel, None] = await self.fetch_channel(
                CHAN_HOF
            )
            raw_message_history: list[discord.Message] = [
                message async for message in hof_channel.history(limit=123)
            ]

        logger.info("Checking for duplicate messages")
        duplicate = False
        for raw_message in raw_message_history:
            if (
                len(raw_message.embeds) > 0
                and str(reaction_message.id) in raw_message.embeds[0].footer.text
            ):
                logger.info("Duplicate message found")
                duplicate = True
                break
        del raw_message_history

        file = None

        if not duplicate:
            if not hof:
                logger.info("Creating Hall of Shame Embed")
                embed_title = (
                    f"{slowpoke_emoji * 3} Hall of Shame Message {slowpoke_emoji * 3}"
                )
                embed_description = (
                    "Messages so shameful they had to be memorialized forever!"
                )
                channel = hos_channel

                file = makeSlowking(payload.member)
            else:
                logger.info("Creating Hall of Fame Embed")
                embed_title = f"{'🏆' * 3} Hall of Shame Message {'🏆' * 3}"
                embed_description = (
                    "Messages so amazing they had to be memorialized forever!"
                )
                channel = hof_channel

            # avatar_url = (
            #     str(reaction_message.author.avatar_url)
            #     .split("?")[0]
            #     .replace("webp", "png")
            # )

            embed = buildEmbed(
                title=embed_title,
                description=embed_description,
                # thumbnail=slowking_path if not None else None,
                file=file if file else None,
                fields=[
                    ["Author", reaction_message.author.mention],
                    ["Message", reaction_message.content],
                    [
                        "Message Link",
                        f"[Click to view message]({reaction_message.jump_url})",
                    ],
                ],
                footer=f"Message ID: {reaction_message.id} | Hall of Shame message created at {reaction_message.created_at.strftime('%B %d, %Y at %H:%M%p')}",
            )
            await channel.send(embed=embed)

    # noinspection PyMethodMayBeStatic
    def get_change_log(self) -> [str, ChangelogException]:
        try:
            changelog_path = None
            changelog_file = "changelog.md"

            if DEBUGGING_CODE:
                changelog_path = pathlib.PurePath(
                    f"{pathlib.Path(__file__).parent.parent.resolve()}/{changelog_file}"
                )
            elif "Linux" in platform.platform():
                changelog_path = pathlib.PurePosixPath(
                    f"{pathlib.Path(__file__).parent.parent.resolve()}/{changelog_file}"
                )
            else:
                logger.exception("Unknown platform. Exiting", exc_info=True)

            changelog = open(changelog_path, "r")
            lines = changelog.readlines()
            lines_str = ""

            for line in lines:
                lines_str += f"* {str(line)}"

            return lines_str
        except OSError:
            logger.exception("Error loading the changelog!", exc_info=True)

    # noinspection PyMethodMayBeStatic
    async def send_welcome_message(
        self, guild_member: Union[discord.Member, discord.User]
    ) -> None:
        channel_general: DISCORD_CHANNEL_TYPES = await self.fetch_channel(CHAN_GENERAL)
        embed = buildEmbed(
            title="New Husker fan!",
            description="Welcome the new member to the server!",
            fields=[
                dict(
                    name="New Member",
                    value=f"{guild_member.display_name}#{guild_member.discriminator}",
                ),
                dict(
                    name="Info",
                    value=f"Be sure to check out `/commands` for how to use the bot!",
                ),
            ],
        )
        await channel_general.send(embed=embed)

    # noinspection PyMethodMayBeStatic
    async def create_online_message(self) -> None:
        return buildEmbed(
            title="Welcome to the Huskers server!",
            description="The official Husker football discord server",
            thumbnail="https://cdn.discordapp.com/icons/440632686185414677/a_061e9e57e43a5803e1d399c55f1ad1a4.gif",
            fields=[
                dict(
                    name="Rules",
                    value=f"Please be sure to check out the rules channel to catch up on server rules.",
                ),
                dict(
                    name="Commands",
                    value=f"View the list of commands with the `/commands` command. Note: Commands do not work in Direct Messages.",
                ),
                dict(
                    name="Hall of Fame & Shame Reaction Threshold",
                    value=str(self.reaction_threshold),
                ),
                dict(
                    name="Version",
                    value=_version,
                ),
                dict(
                    name="Changelog",
                    value=self.get_change_log(),
                ),
                dict(
                    name="Support Bot Frost",
                    value="Check out `/donate` to see how you can support the project!",
                ),
            ],
        )

    # noinspection PyMethodMayBeStatic
    async def on_connect(self) -> None:
        logger.info("The bot has connected!")

    # noinspection PyMethodMayBeStatic
    async def on_ready(self) -> None:
        self.guild_user_len = len(self.users)
        self.reaction_threshold = int(0.0047 * self.guild_user_len)
        chan_botspam: discord.TextChannel = await self.fetch_channel(CHAN_BOT_SPAM)

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
                # It will also NOT currently output a traceback. You MUST investigate
                # manually by stepping through code until I find a way to capture these
                # exceptions.

                await self.load_extension(extension)
                logger.info(f"Loaded the [{extension}] extension")
            except Exception as e:  # noqa
                logger.exception(f"Unable to load the {extension} extension\n{e}")
                continue

        logger.info("All extensions loaded")

        if not DEBUGGING_CODE:
            logger.info("Hiding online message because debugging")
            await chan_botspam.send(embed=await self.create_online_message())  # noqa

        logger.info("The bot is ready!")

        try:
            logger.info("Attempting to sync the bot tree")
            await self.tree.sync(guild=discord.Object(id=GUILD_PROD))
        except Exception as e:  # noqa
            logger.exception("Error syncing the tree!")

        logger.info("The bot tree has synced!")

        # if DEBUGGING_CODE:
        #     return

        logger.info("Collecting open reminders")
        open_reminders = processMySQL(query=sqlRetrieveReminders, fetch="all")

        async def convertDestination(raw_send_to: str) -> discord.TextChannel:
            logger.info("Attempting to fetch destination")
            try:
                dest: Union[discord.TextChannel, None] = await self.fetch_channel(
                    int(raw_send_to)
                )
            except NotFound:
                dest = await self.fetch_channel(CHAN_BOT_SPAM)
                pass

            logger.info(f"destination is {dest.name.encode('utf-8')}")
            return dest

        async def convertSentTo(raw_send_to: str) -> Union[discord.User, None]:
            logger.info("Attempting to fetch remind_who")
            try:
                send_to: Union[discord.User, None] = await self.fetch_user(
                    int(raw_send_to)
                )
                logger.info(
                    f"remind_who is {send_to.name.encode('utf-8')}#{send_to.discriminator}"
                )
            except NotFound:
                send_to = None
                logger.info("remind_who is None")
                pass

            return send_to

        tasks: list[MissedReminder] = []
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
                        logger.error(
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
                    logger.info(
                        f"Adding reminder for/to [{reminder['send_to']}] to task list."
                    )

                    tasks.append(
                        MissedReminder(
                            duration=duration,
                            author=reminder["author"],
                            destination=destination,
                            message=reminder["message"],
                            remind_who=remind_who,
                            missed_reminder=True,
                        )
                    )
            logger.info("Compiled all open tasks")
        else:
            logger.info("No open reminders found")

        # TODO This is blocking all code below
        # logger.info("Processing task lists")
        # [await task.run() for task in tasks]

        if DEBUGGING_CODE:
            embed = buildEmbed(
                title="Reminders",
                description=f"There were {len(open_reminders) + 1} loaded!",
            )
            await chan_botspam.send(embed=embed)

        logger.info("Open reminders restarted")

        logger.info("Starting Twitter stream")
        start_twitter_stream(self)
        logger.info("Twitter stream started")

    async def on_member_join(self, guild_member: discord.Member) -> None:
        await self.send_welcome_message(guild_member)

    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        await self.check_reaction(payload)
