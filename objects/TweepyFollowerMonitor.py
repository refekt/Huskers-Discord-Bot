import logging
import platform
from typing import Optional, Any, Union

import discord
import schedule
import tweepy

from helpers.constants import (
    DEBUGGING_CODE,
    CHAN_BOT_SPAM_PRIVATE,
    CHAN_TWITTERVERSE,
    CHAN_GENERAL,
    ROLE_EVERYONE_PROD,
)
from helpers.embed import buildTweetEmbed
from helpers.misc import general_locked
from objects.Exceptions import TwitterFollowerException
from objects.Logger import discordLogger

asyncio_logger = discordLogger(
    name="asyncio", level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if "Windows" in platform.platform() else logging.INFO,
)


class TwitterListMember:
    def __init__(self, client: tweepy.Client, member_data):
        self.client: tweepy.Client = client
        self.user_id: Optional[Union[int, str]] = member_data["id"]
        self.name: Optional[str] = member_data["name"]
        self.usernamename: Optional[str] = member_data["username"]
        self.orig_followers: Optional[Union[dict, Any]] = None
        self.new_followers: Optional[Union[dict, Any]] = None

        self._collect_users(initial=True)

    def _collect_users(self, initial: bool) -> None:
        if initial:
            self.orig_followers = self.client.get_users_following(id=self.user_id)
        else:
            self.new_followers = self.client.get_users_following(id=self.user_id)

    @property
    def differences(self):  # TODO Type hinting
        # TODO Not sure if this all works.
        self._collect_users(initial=False)

        if not self.new_followers:
            return

        return set(self.orig_followers) ^ set(self.new_followers)


async def send_tweet(client: discord.Client, member: TwitterListMember) -> None:
    # class TwitterButtons(discord.ui.View):
    #     def __init__(
    #         self,
    #         timeout=1200,
    #     ) -> None:
    #         super(TwitterButtons, self).__init__()
    #         self.message: Optional[discord.Message] = None
    #         self.timeout = timeout
    #         self.client = client
    #
    #     async def on_timeout(self) -> None:
    #         tweepy_client_logger.debug(
    #             "Twitter buttons have timed out. Removing all buttons"
    #         )
    #
    #         self.clear_items()
    #         await self.message.edit(view=self)
    #
    #     # noinspection PyMethodMayBeStatic
    #     def grabTwitterLink(self, message_embed: discord.Embed) -> str:
    #         link: list[str] = [
    #             field.value
    #             for field in message_embed.fields
    #             if field.name == "Link to Tweet"
    #         ]
    #         return "".join(link)
    #
    #     @discord.ui.button(
    #         label="Send to General",
    #         custom_id="send_to_general",
    #         style=discord.ButtonStyle.gray,
    #     )
    #     async def send_to_general(
    #         self, interaction: discord.Interaction, button: discord.ui.Button
    #     ):
    #         tweepy_client_logger.debug("Sending tweet to general channel")
    #
    #         general_channel: discord.TextChannel = await self.client.fetch_channel(
    #             CHAN_GENERAL
    #         )
    #
    #         if general_locked(
    #             general_channel, self.client.guilds[0].get_role(ROLE_EVERYONE_PROD)
    #         ):
    #             tweepy_client_logger.debug(
    #                 "Game day mode is on. Will send tweets to live discussion."
    #             )
    #             general_channel = await self.client.fetch_channel(CHAN_DISCUSSION_LIVE)
    #
    #         await general_channel.send(
    #             f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
    #         )
    #         await interaction.response.send_message("Tweet forwarded!", ephemeral=True)
    #
    #     @discord.ui.button(
    #         label="Send to Recruiting",
    #         custom_id="send_to_recruiting",
    #         style=discord.ButtonStyle.gray,
    #     )
    #     async def send_to_recruiting(
    #         self, interaction: discord.Interaction, button: discord.ui.Button
    #     ):
    #         tweepy_client_logger.debug("Sending tweet to recruiting channel")
    #
    #         recruiting_channel = await self.client.fetch_channel(CHAN_RECRUITING)
    #
    #         if general_locked(
    #             recruiting_channel, self.client.guilds[0].get_role(ROLE_EVERYONE_PROD)
    #         ):
    #             tweepy_client_logger.debug(
    #                 "Game day mode is on. Will send tweets to streaming discussion."
    #             )
    #             recruiting_channel = await self.client.fetch_channel(
    #                 CHAN_DISCUSSION_STREAMING
    #             )
    #
    #         await recruiting_channel.send(
    #             f"{interaction.user.name}#{interaction.user.discriminator} forwarded the following tweet: {self.grabTwitterLink(interaction.message.embeds[0])}"
    #         )
    #         await interaction.response.send_message("Tweet forwarded!", ephemeral=True)

    logger.debug(f"Sending a tweet...")

    if DEBUGGING_CODE:
        twitter_channel: discord.TextChannel = await client.fetch_channel(
            CHAN_BOT_SPAM_PRIVATE
        )
    else:
        twitter_channel = await client.fetch_channel(CHAN_TWITTERVERSE)

    embed = buildTweetEmbed(response=response)

    # author: User = response.includes["users"][0]

    # view: TwitterButtons = TwitterButtons()

    test_channel: discord.TextChannel = await client.fetch_channel(CHAN_GENERAL)

    if general_locked(test_channel, client.guilds[0].get_role(ROLE_EVERYONE_PROD)):
        view.children[0].label = "Send to Live"  # noqa
        view.children[1].label = "Send to Streaming"  # noqa

    # view.add_item(
    #     item=discord.ui.Button(
    #         style=discord.ButtonStyle.url,
    #         label="Open Tweet...",
    #         url=f"https://twitter.com/{author.username}/status/{response.data.id}",
    #     )
    # )
    # view.message = await twitter_channel.send(embed=embed, view=view)
    # logger.debug("Waiting for twitter buttons to be pushed")

    # asyncio.run_coroutine_threadsafe(coro=view.wait(), loop=client.loop)

    logger.info(f"Tweet sent!")


class TwitterFollowerMonitor:
    def __init__(self, client: tweepy.Client, members: Union[dict, Any]):
        self.client: tweepy.Client = client
        self.list_members: Optional[list[TwitterListMember]] = self._setup_list_members(
            members=members
        )
        asyncio_logger.debug("Creating Twitter Follower Monitor")

        self._setup_schedule()

    def _setup_list_members(self, members: Union[dict, Any]) -> list[TwitterListMember]:
        return [
            TwitterListMember(client=self.client, member_data=member)
            for member in members
        ]

    def check_differences(self):
        asyncio_logger.debug("Attempting to check for Twitter Follower differences")

        assert self.list_members, TwitterFollowerException("Error")

        for member in self.list_members:
            continue

    @property
    def all_jobs(self) -> str:
        all_jobs: list[schedule.Job] = schedule.jobs
        all_jobs_str: str = ""
        for job in all_jobs:
            all_jobs_str += f"* {repr(job)}\n"

        return all_jobs_str

    def _setup_schedule(self) -> None:
        asyncio_logger.debug("Setting up Twitter Monitor Follower schedule")

        schedule.every().hour.do(self.check_differences)

        asyncio_logger.debug(
            f"Scheduled messages complete. Jobs are:\n\n{self.all_jobs}"
        )
