# TODO
# * Bot status updates
# * Client events
# * Hall of Fame/Shame
# * Iowa checks
# * Reminders
# * Twitter stream
# TODO

import inspect
import logging
import pathlib
import platform

import interactions

from helpers.constants import (
    PROD_TOKEN,
    TEST_TOKEN,
    CHAN_BOT_SPAM,
    GUILD_PROD,
    CHAN_ANNOUNCEMENT,
)
from helpers.embed import buildEmbed
from helpers.misc import convertEmbedtoDict, getUserMention, getChannelMention
from objects.Exceptions import CommandException

__author__ = "u/refekt"
__version__ = "3.5.0"

CUR_TOKEN = PROD_TOKEN  # TEST_TOKEN

bot = interactions.Client(
    token=CUR_TOKEN, intents=interactions.Intents.ALL, log_level=logging.CRITICAL
)
__all__ = ["bot"]

# Get rid of d-p-i.py spam
bot_loggers = ["client", "context", "dispatch", "gateway", "http", "mixin"]
for logger in bot_loggers:
    logging.getLogger(logger).handlers.clear()

logger = logging.getLogger(f"{__name__}-frost")

reaction_threshold = 12


def getWelcomeMessage() -> interactions.Embed:
    return buildEmbed(
        title="Welcome to the Huskers server!",
        description="The official Husker football discord server",
        thumbnail="https://cdn.discordapp.com/icons/440632686185414677/a_061e9e57e43a5803e1d399c55f1ad1a4.gif",
        fields=[
            [
                "Rules",
                f"Please be sure to check out the rules channel to catch up on server rules.",
            ],
            [
                "Commands",
                f"View the list of commands with the `/commands` command. Note: Commands do not work in Direct Messages.",
            ],
            [
                "Roles",
                "You can assign yourself come flair by using the `/roles` command.",
            ],
        ],
        inline=False,
    )


async def getServerStatistics(client: interactions.Client) -> str:
    guild = await client.http.get_guild(guild_id=GUILD_PROD)
    description = guild.get("description", "N/A")
    features_raw = guild.get("features", [])
    features_raw.sort()
    features = ", ".join(features_raw).replace("_", " ").title()
    owner = getUserMention(
        user=await client.http.get_user(user_id=guild.get("owner_id"))
    )
    region = guild.get("region", "N/A")
    vanity_url = (
        f"https://discord.gg/{guild.get('vanity_url_code')}"
        if guild.get("vanity_url_code")
        else "N/A"
    )
    boost_count = guild.get("premium_subscription_count", "N/A")
    server_stats = (
        f"• __Onwer:__ {owner}\n"
        f"• __Description:__ {description}\n"
        f"• __Server Features:__ {features}\n"
        f"• __Server Region:__ {region}\n"
        f"• __Vanity URL:__ {vanity_url}\n"
        f"• __Boost Count:__ {boost_count}\n"
        f"• __Rules Channel:__ {getChannelMention(CHAN_ANNOUNCEMENT)}"
    )
    return server_stats


def getChangelog() -> [str, CommandException]:
    try:
        changelog_path = None

        if "Windows" in platform.platform():
            changelog_path = pathlib.PurePath(
                f"{pathlib.Path(__file__).parent.resolve()}/changelog.md"
            )
        elif "Linux" in platform.platform():
            changelog_path = pathlib.PurePosixPath(
                f"{pathlib.Path(__file__).parent.resolve()}/changelog.md"
            )

        changelog = open(changelog_path, "r")
        lines = changelog.readlines()
        lines_str = ""

        for line in lines:
            lines_str += f"* {str(line)}"

        return lines_str
    except OSError:
        return CommandException("Error loading changelog.")


async def getOnlineMessage() -> interactions.Embed:
    return buildEmbed(
        title="Husker Discord Bot",
        fields=[
            [
                "Info",
                f"I was restarted, but now I'm back! Check out `/` to see what I can do!",
            ],
            ["Bot Version", __version__],
            ["Server Insights", await getServerStatistics(bot)],
            ["HOF & HOS Reaction Threshold", reaction_threshold],
            ["Changelog", getChangelog()],
            [
                "More Changelog",
                f"[View rest of commits](https://github.com/refekt/Bot-Frost/commits/master)",
            ],
        ],
        inline=False,
    )


# TODO Waiting for d-p-i.py to add `MessageReaction` attribute
def surpassedReactionThreshold(reaction: interactions.Reaction) -> bool:
    return True


# Events


@bot.event
async def on_ready():
    try:
        await bot.http.send_message(
            channel_id=CHAN_BOT_SPAM,
            content="",
            tts=False,
            embeds=[convertEmbedtoDict(await getOnlineMessage())],
            nonce=None,
            allowed_mentions=None,
            message_reference=None,
        )
    except Exception as err:
        logger.error(f"Exception received: {err}")

    logger.info("The bot is ready!")


@bot.event
async def on_guild_member_add(guild_member: interactions.GuildMember):
    # TODO d-p-i.py is slated to add `send()` to Member, Channel, etc. models
    try:
        await bot.http.send_message(
            channel_id=guild_member.user.id,
            content="",
            embeds=[convertEmbedtoDict(getWelcomeMessage())],
        )
    except Exception:
        raise CommandException(
            f"Unable to send message to {guild_member.user.username}"
        )


@bot.event
async def on_guild_member_remove(guild_member: interactions.GuildMember):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_member_update(guild_member: interactions.GuildMember):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_create(role: interactions.Role):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_update(role: interactions.Role):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_role_delete(role: interactions.Role):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


# TODO Capture metrics for guild karma
# @bot.event
# async def on_message_create(message: interactions.Message):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Botlogs record?
# @bot.event
# async def on_message_update(message: interactions.Message):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Botlogs record?
# @bot.event
# async def on_message_delete(message: interactions.Message):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)


# TODO Purge commands?
# @bot.event
# async def on_message_delete_bulk(
#     message_ids, channel: interactions.Channel, guild: interactions.Guild
# ):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)


@bot.event
async def on_channel_pins_update(pin: interactions.ChannelPins):
    logger.info(f"A a pin was updated in {pin.channel_id}")


@bot.event
async def on_invite_create(
    invite: interactions.Invite,
):
    inviter = invite._json.get("inviter")
    code = invite._json.get("code")

    logger.info(
        f"{inviter['username']}#{inviter['discriminator']} created the {'permanent' if invite.temporary else 'temporary'} invite code {code} at {invite.created_at}.",
    )


@bot.event
async def on_guild_scheduled_event_create(
    scheduled_event: interactions.ScheduledEvents,
):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_update(
    scheduled_event: interactions.ScheduledEvents,
):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_delete(
    scheduled_event: interactions.ScheduledEvents,
):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_user_add(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_scheduled_event_user_remove(
    scheduled_event: interactions.ScheduledEvents,
    user: interactions.User,
    guild: interactions.Guild,
):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_invite_delete(invite: interactions.Invite):
    logger.info(f"The invite code {invite._json.get('code')} was deleted.")


@bot.event
async def on_guild_create(guild: interactions.Guild):
    logger.info(f"Establishing guild connection to: {guild.name}")


@bot.event
async def on_guild_update(guild: interactions.Guild):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_delete(guild: interactions.Guild):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_emojis_update(emojis: interactions.GuildEmojis):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


@bot.event
async def on_guild_stickers_update(stickers: interactions.GuildStickers):
    logger.info(f"Loaded {inspect.stack()[0][3]}")


# TODO d-p-i.py bug
# @bot.event
# async def on_guild_ban_add(user: interactions.User):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_guild_ban_remove(user: interactions.User):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_create(
#     channel: interactions.Channel, thread_member: interactions.ThreadMember = None
# ):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_update(channel: interactions.Channel):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_delete(channel: interactions.Channel):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_list_sync():
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_member_update(thread_member: interactions.ThreadMember):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_thread_members_update(thread_member: interactions.ThreadMember):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_message_reaction_add(
#     reaction: interactions.Reaction,
# ):
#     test = surpassedReactionThreshold(reaction)
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
#
#
# @bot.event
# async def on_message_reaction_remove(
#     reaction: interactions.Reaction
# ):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_message_reaction_remove_all(
#     channel: interactions.Channel,
#     message: interactions.Message,
#     guild: interactions.Guild,
# ):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)
#
#
# @bot.event
# async def on_message_reaction_remove_emoji(
#     channel: interactions.Channel,
#     message: interactions.Message,
#     guild: interactions.Guild,
#     emoji: interactions.Emoji = None,
# ):
#     logger.info(f"Loaded {inspect.stack()[0][3]}", 0)

# Events

# Commands


@bot.command(
    type=interactions.ApplicationCommandType.CHAT_INPUT,
    name="about",
    description="About the bot!",
    scope=GUILD_PROD,
)
async def _about(ctx: interactions.CommandContext) -> None:
    embed: interactions.Embed = buildEmbed(
        title="About Me",
        fields=[
            [
                "History",
                "Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt). [/u/psyspoop](https://reddit.com/u/psyspoop), Jeyrad, and ModestBeaver greatly assisted with the creation.",
            ],
            [
                "Source Code",
                "[GitHub](https://www.github.com/refekt/Husker-Bot)",
            ],
            [
                "Hosting Location",
                f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}",
            ],
            [
                "Hosting Status",
                f"{'Lol' if 'Windows' in platform.platform() else 'https://status.hyperexpert.com/'}",
            ],
            ["Latency", f"TBD"],
            ["Username", getUserMention(bot.me)],
            ["Birthday", f"I was born on ..."],
            [
                "Feeling generous?",
                f"Check out `/donate` to help out the production and upkeep of the bot.",
            ],
        ],
        inline=False,
    )

    await ctx.send(
        content="",
        embeds=[embed],
    )


# Commands


@bot.event
async def on_user_update(user: interactions.User):
    logger.info(f"Loaded {inspect.stack()[0][3]}")
