import logging
import pathlib
import platform
from typing import Union

import discord
import tweepy
from discord.ext.commands import (
    Bot,
)

from __version__ import _version
from helpers.constants import (
    CHAN_BOT_SPAM,
    CHAN_GENERAL,
    DISCORD_CHANNEL_TYPES,
    GUILD_PROD,
    TWITTER_BEARER,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_QUERY_MAX,
)
from helpers.embed import buildEmbed
from objects.Exceptions import CommandException, ExtensionException
from objects.TweepyStreamListener import StreamClientV2

logger = logging.getLogger(__name__)

__all__ = ["HuskerClient"]

logger.info(f"{str(__name__).title()} module loaded!")

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


# async def send_tweet(tweet):
#     if tweet.author.id_str not in [member["id_str"] for member in list_members]:
#         return
#
#     direct_url = f"https://twitter.com/{tweet.author.screen_name}/status/{tweet.id_str}"
#
#     if hasattr(tweet, "extended_tweet"):
#         fields = [
#             dict(
#                 name="Message",
#                 value=tweet.extended_tweet["full_text"],
#                 inline=False,
#             )
#         ]
#     else:
#         fields = [dict(name="Message", value=tweet.text, inline=False)]
#
#     fields.append(dict(name="URL", value=direct_url, inline=False))
#
#     embed = buildEmbed(
#         title="Husker Tweet",
#         url="https://twitter.com/i/lists/1307680291285278720",
#         fields=fields,
#         footer=f"Tweet sent {tweet.created_at.strftime(DT_TWEET_FORMAT)}",
#     )
#
#     embed.set_author(
#         name=f"{tweet.author.name} (@{tweet.author.screen_name}) via {tweet.source}",
#         icon_url=tweet.author.profile_image_url_https,
#     )
#
#     # TODO Work in Progress to capture all attached media
#     if hasattr(tweet, "extended_entities"):
#         try:
#             for index, media in enumerate(tweet.extended_entities["media"]):
#                 if index == 0:
#                     embed.set_image(
#                         url=tweet.extended_entities["media"][index]["media_url"]
#                     )
#                 embed.add_field(
#                     name=f"Media #{index + 1}",
#                     value=f"[Link #{index + 1}]({media['media_url']})",
#                     inline=False,
#                 )
#         except Exception as e:  # noqa
#             logger.warning(f"send_tweet exceptoin\n{e}")
#             pass
#
#     logger.info(f"Sending tweet from @{tweet.author.screen_name}")
#
#     if tweet.author.screen_name.lower() == TWITTER_BLOCK16_SCREENANME.lower():
#         chan: discord.TextChannel = self.get_channel(CHAN_FOOD)
#         await chan.send(embed=embed)
#     else:
#         view = TwitterButtons()
#         chan: discord.TextChannel = self.get_channel(CHAN_TWITTERVERSE)
#         await chan.send(view=view, embed=embed)


def start_twitter_stream() -> None:
    logger.info("Bot is starting the Twitter stream")

    logger.info("Getting Husker Media Twitter list")
    tweeter_client = tweepy.Client(TWITTER_BEARER)
    list_members = tweeter_client.get_list_members(TWITTER_HUSKER_MEDIA_LIST_ID)

    logger.info("Creating stream rule")
    rule_query = ""
    if "Windows" in platform.platform():
        rule_query = "from:ayy_gbr OR "
    for member in list_members[0]:
        append_str = f"from:{member['username']} OR "

        if len(rule_query) + len(append_str) < TWITTER_QUERY_MAX:
            rule_query += append_str
        else:
            break
    rule_query = rule_query[:-4]  # Get rid of ' OR '

    logger.info("Creating a stream client")
    tweeter_stream = StreamClientV2(
        bearer_token=TWITTER_BEARER,
        wait_on_rate_limit=True,
        max_retries=3,
    )

    logger.info(f"Created stream rule:\n\t{rule_query}")
    tweeter_stream.add_rules(tweepy.StreamRule(value=rule_query))
    logger.info(f"Stream filter rules:\n\t{tweeter_stream.get_rules()}")

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


class TwitterButtons(discord.ui.View):
    @discord.ui.button(
        label="Send to General",
        custom_id="send_to_general",
        style=discord.ButtonStyle.gray,
    )
    async def send_to_general(self):
        ...

    @discord.ui.button(
        label="Send to Recruiting",
        custom_id="send_to_recruiting",
        style=discord.ButtonStyle.gray,
    )
    async def send_to_general(self):
        ...

    # NOTE Discord API preventing creating a URL button at this scope


class HuskerClient(Bot):
    CommandEnums = None

    add_extensions = [
        "commands.admin",
        "commands.football_stats",
        "commands.image",
        "commands.recruiting",
        "commands.reminder",
        "commands.text",
    ]

    async def setup_hook(self) -> None:
        logger.info("Starting Twitter stream")
        start_twitter_stream()
        logger.info("Twitter stream started")

    # noinspection PyMethodMayBeStatic
    def get_change_log(self) -> [str, CommandException]:
        try:
            changelog_path = None
            changelog_file = "changelog.md"

            if "Windows" in platform.platform():
                changelog_path = pathlib.PurePath(
                    f"{pathlib.Path(__file__).parent.parent.resolve()}/{changelog_file}"
                )
            elif "Linux" in platform.platform():
                changelog_path = pathlib.PurePosixPath(
                    f"{pathlib.Path(__file__).parent.parent.resolve()}/{changelog_file}"
                )

            changelog = open(changelog_path, "r")
            lines = changelog.readlines()
            lines_str = ""

            for line in lines:
                lines_str += f"* {str(line)}"

            return lines_str
        except OSError:
            logger.warning("Error loading the changelog!")
            raise CommandException("Error loading the changelog!")

    # noinspection PyMethodMayBeStatic
    async def create_welcome_message(
        self, guild_member: Union[discord.Member, discord.User]
    ) -> None:
        channel_general: DISCORD_CHANNEL_TYPES = await self.fetch_channel(CHAN_GENERAL)
        embed = buildEmbed(
            title="New Husker fan!",
            description="Welcome the new member to the server!",
            fields=[
                dict(name="New Member", value=guild_member.mention, inline=False),
                dict(
                    name="Info",
                    value=f"Be sure to check out `/commands` for how to use the bot!",
                    inline=False,
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
                    inline=False,
                ),
                dict(
                    name="Commands",
                    value=f"View the list of commands with the `/commands` command. Note: Commands do not work in Direct Messages.",
                    inline=False,
                ),
                dict(
                    name="Hall of Fame & Shame Reaaction Threshold",
                    value="TBD",
                    inline=False,
                ),
                dict(name="Version", value=_version, inline=False),
                dict(name="Changelong", value=self.get_change_log(), inline=False),
                dict(
                    name="Support Bot Frost",
                    value="Check out `/donate` to see how you can support the project!",
                    inline=False,
                ),
            ],
        )

    # async def check_reaction(self, reaction: discord.Reaction):
    #     ...

    # noinspection PyMethodMayBeStatic
    async def on_connect(self) -> None:
        logger.info("The bot has connected!")

    # noinspection PyMethodMayBeStatic
    async def on_ready(self) -> None:
        logger.info("Loading extensions")

        for extension in self.add_extensions:
            try:
                # NOTE Extensions will fail to load when runtime errors exist in the code.
                # It will also NOT currently output a traceback. You MUST investigate
                # mannually by stepping through code until I find a way to capture these
                # exceptions.
                await self.load_extension(extension)
                logger.info(f"Loaded the {extension} extension")
            except Exception as e:  # noqa
                logger.error(f"ERROR: Unable to laod the {extension} extension\n{e}")
                raise ExtensionException(
                    f"ERROR: Unable to laod the {extension} extension\n{e}"
                )

        logger.info("All extensions loaded")

        chan_botspam: discord.TextChannel = await self.fetch_channel(CHAN_BOT_SPAM)
        # await chan_botspam.send(embed=await self.create_online_message())  # noqa

        logger.info("The bot is ready!")

        try:
            await self.tree.sync(guild=discord.Object(id=GUILD_PROD))
        except Exception as e:  # noqa
            logger.error("Error syncing the tree!\n\n{e}")

        logger.info("The bot tree has synced!")

    async def on_member_join(
        self, guild_member: Union[discord.Member, discord.User]
    ) -> None:
        await self.create_welcome_message(guild_member)

    async def on_error(self, event_method, *args, **kwargs) -> None:  # TODO
        # logger.info(f"On Error\n{event_method}\n{args}\n{kwargs}")
        ...

    async def on_command_error(self, context, exception) -> None:  # TODO
        logger.info(f"On Command Error\n{context}{exception}")

    async def on_message_reaction_add(
        self,
        reaction: discord.Reaction,
    ) -> None:  # TODO
        ...  # await self.check_reaction(reaction)
