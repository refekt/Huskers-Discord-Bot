# TODO
# * Bot status updates
# * Client events
# * Hall of Fame/Shame
# * Iowa checks
# * Reminders
# * Twitter stream
# TODO

import logging
import pathlib
import platform
from typing import Union, Any

import discord
from discord.ext.commands import Bot

from helpers.constants import CHAN_BOT_SPAM, CHAN_GENERAL
from helpers.embed import buildEmbed
from objects.Exceptions import CommandException

logger = logging.getLogger(__name__)

__all__ = ["HuskerClient"]

logger.info(f"{str(__name__).title()} module loaded!")

discord_channel_types = Union[
    discord.abc.GuildChannel, discord.abc.PrivateChannel, discord.TextChannel, Any
]

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


class HuskerClient(Bot):
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
    ):
        channel_general: discord_channel_types = await self.fetch_channel(
            channel_id=CHAN_GENERAL
        )

        await channel_general.send(
            content=f"New guild member alert: welcome to {guild_member.mention}!"
        )

    # noinspection PyMethodMayBeStatic
    async def create_online_message(self):
        return buildEmbed(
            title="Welcome to the Huskers server!",
            description="The official Husker football discord server",
            thumbnail="https://cdn.discordapp.com/icons/440632686185414677/a_061e9e57e43a5803e1d399c55f1ad1a4.gif",
            fields=[
                {
                    "name": "Rules",
                    "value": f"Please be sure to check out the rules channel to catch up on server rules.",
                    "inline": False,
                },
                {
                    "name": "Commands",
                    "value": f"View the list of commands with the `/commands` command. Note: Commands do not work in Direct Messages.",
                    "inline": False,
                },
                {
                    "name": "Hall of Fame & Shame Threshold",
                    "value": "TBD",
                    "inline": False,
                },
                {"name": "Changelog", "value": self.get_change_log(), "inline": False},
                {
                    "name": "Complete Changelog",
                    "value": "https://github.com/refekt/Bot-Frost/commits/master",
                    "inline": False,
                },
                {
                    "name": "Support HuskerBot",
                    "value": "Check out `/donate` to see how you can support the project!",
                    "inline": False,
                },
            ],
        )

    # async def check_reaction(self, reaction: discord.Reaction):
    #     ...

    # noinspection PyMethodMayBeStatic
    async def on_connect(self):
        logger.info("The bot has connected!")

    # noinspection PyMethodMayBeStatic
    async def on_ready(self):
        logger.info("The bot is ready!")

        chan_botspam: discord_channel_types = await self.fetch_channel(
            channel_id=CHAN_BOT_SPAM
        )

        online_message = await self.create_online_message()

        await chan_botspam.send(content="", embed=online_message)

    # async def on_message_reaction_add(
    #     self,
    #     reaction: discord.Reaction,
    # ):
    #     await self.check_reaction(reaction)

    async def on_member_join(self, guild_member: Union[discord.Member, discord.User]):
        await self.create_welcome_message(guild_member)

    # async def on_error(self, event_method, *args, **Kwargs):
    #     ...

    # async def on_command_error(self, context, exception):
    #     ...
