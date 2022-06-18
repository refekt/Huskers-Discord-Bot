import pathlib
import platform
import subprocess
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Union

import discord.ext.commands
from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands

from __version__ import _version
from helpers.constants import (
    BOT_FOOTER_SECRET,
    CAT_GAMEDAY,
    CAT_GENERAL,
    CHAN_ADMIN,
    CHAN_DISCUSSION_LIVE,
    CHAN_DISCUSSION_STREAMING,
    CHAN_GENERAL,
    CHAN_HYPE_GROUP,
    CHAN_IOWA,
    CHAN_RECRUITING,
    DISCORD_USER_TYPES,
    GUILD_PROD,
    ROLE_EVERYONE_PROD,
    ROLE_TIME_OUT,
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter
from helpers.mysql import processMySQL, sqlInsertIowa, sqlRetrieveIowa, sqlRemoveIowa
from objects.Client import start_twitter_stream
from objects.Exceptions import CommandException, UserInputException, SSHException
from objects.Logger import discordLogger
from objects.Paginator import EmbedPaginatorView
from objects.Thread import wait_and_run

logger = discordLogger(__name__)


class ConfirmButtons(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()


class AdminCog(commands.Cog, name="Admin Commands"):
    class MammalChannels(Enum):
        general = 1
        recruiting = 2
        admin = 3

    group_purge = app_commands.Group(
        name="purge",
        description="Purge messages from channel",
        default_permissions=discord.Permissions(administrator=True),
        guild_ids=[GUILD_PROD],
    )
    group_submit = app_commands.Group(
        name="submit",
        description="Submit a bug or feature request for the bot",
        guild_ids=[GUILD_PROD],
    )
    group_gameday = app_commands.Group(
        name="gameday",
        description="Turn game day mode on or off",
        default_permissions=discord.Permissions(manage_messages=True),
        guild_ids=[GUILD_PROD],
    )
    group_restart = app_commands.Group(
        name="restart",
        description="Restart elements of the bot",
        default_permissions=discord.Permissions(manage_messages=True),
        guild_ids=[GUILD_PROD],
    )

    # noinspection PyMethodMayBeStatic
    async def alert_gameday_channels(
        self, client: Union[discord.ext.commands.Bot, discord.Client], on: bool
    ) -> None:
        chan_general = await client.fetch_channel(CHAN_GENERAL)
        chan_live = await client.fetch_channel(CHAN_DISCUSSION_LIVE)
        chan_streaming = await client.fetch_channel(CHAN_DISCUSSION_STREAMING)

        if on:
            embed = buildEmbed(
                title="Game Day Mode",
                description="Game day mode is now on!",
                fields=[
                    dict(
                        name="Live TV",
                        value=f"{chan_live.mention} text and voice channels are for users who are watching live.",
                    ),
                    dict(
                        name="Streaming",
                        value=f"{chan_streaming.mention} text and voice channels are for users who are streaming the game.",
                    ),
                    dict(
                        name="Info",
                        value="All channels in the Huskers category will be turned off until the game day mode is disabled.",
                    ),
                ],
            )
        else:
            embed = buildEmbed(
                title="Game Day Mode",
                description="Game day mode is now off!",
                fields=[
                    dict(
                        name="Info",
                        value=f"Game day channels have been disabled and General categories channels have been enabled. Regular discussion may continue in {chan_general.mention}.",
                    )
                ],
            )

        await chan_general.send(embed=embed)
        await chan_live.send(embed=embed)
        await chan_streaming.send(embed=embed)

    # noinspection PyMethodMayBeStatic
    async def process_gameday(self, mode: bool, guild: discord.Guild) -> None:
        gameday_category = guild.get_channel(CAT_GAMEDAY)
        general_category = guild.get_channel(CAT_GENERAL)
        everyone = guild.get_role(ROLE_EVERYONE_PROD)

        logger.info(f"Creating permissions to be [{mode}]")

        perms_text = discord.PermissionOverwrite()

        perms_text.view_channel = mode  # noqa
        perms_text.send_messages = mode  # noqa
        perms_text.read_messages = mode  # noqa

        perms_text_opposite = discord.PermissionOverwrite()
        perms_text_opposite.send_messages = not mode  # noqa

        perms_voice = discord.PermissionOverwrite()
        perms_voice.view_channel = mode  # noqa
        perms_voice.connect = mode  # noqa
        perms_voice.speak = mode  # noqa

        logger.info(f"Permissions created")

        for channel in general_category.channels:

            if channel.id in CHAN_HYPE_GROUP:
                continue

            try:
                logger.info(
                    f"Attempting to changes permissions for [{channel}] to [{not mode}]"
                )
                if channel.type == discord.ChannelType.text:
                    await channel.set_permissions(
                        everyone, overwrite=perms_text_opposite
                    )
            except:  # noqa
                logger.info(
                    f"Unable to change permissions for [{channel}] to [{not mode}]"
                )
                continue

            logger.info(f"Changed permissions for [{channel}] to [{not mode}]")

        for channel in gameday_category.channels:
            try:
                logger.info(
                    f"Attempting to changes permissions for [{channel}] to [{mode}]"
                )

                if channel.type == discord.ChannelType.text:
                    await channel.set_permissions(everyone, overwrite=perms_text)
                elif channel.type == discord.ChannelType.voice:
                    await channel.set_permissions(everyone, overwrite=perms_voice)

                    # TODO Trying to kick people from voice channels if game day mode is turned off.
                else:
                    logger.info(
                        f"Unable to change permissions for [{channel}] to [{mode}]"
                    )
                    continue
                logger.info(f"Changed permissions for [{channel}] to [{mode}]")
            except discord.errors.Forbidden:
                logger.exception(
                    "The bot does not have access to change permissions!", exc_info=True
                )
            except:  # noqa
                continue

        logger.info(f"All permissions changes applied")

    # noinspection PyMethodMayBeStatic
    async def college_purge_messages(
        self, channel: Any, all_messages: bool = False
    ) -> list:
        msgs = []
        max_age = datetime.now() - timedelta(
            days=13, hours=23, minutes=59
        )  # Discord only lets you delete 14 day old messages

        try:
            async for message in channel.history(limit=100):
                if (
                    message.created_at >= max_age.astimezone() and message.author.bot
                    if not all_messages
                    else True
                ):
                    msgs.append(message)

        except discord.ClientException:
            logger.exception(
                "Cannot delete more than 100 messages at a time.", exc_info=True
            )
        except discord.Forbidden:
            logger.exception("Missing permissions.", exc_info=True)
        except discord.HTTPException:
            logger.exception(
                "Deleting messages failed. Bulk messages possibly include messages over 14 days old.",
                exc_info=True,
            )

        return msgs

    # noinspection PyMethodMayBeStatic
    async def confirm_purge(self, interaction: discord.Interaction) -> bool:

        view = ConfirmButtons()
        await interaction.response.send_message(
            "Do you want to continue?", view=view, ephemeral=True
        )
        await view.wait()

        if view.value is None:
            logger.exception("Purge confirmation timed out!", exc_info=True)
        elif view.value:
            return True
        else:
            return False

    @app_commands.command(name="about", description="Learn all about Bot Frost")
    @app_commands.guilds(GUILD_PROD)
    async def about(self, interaction: discord.Interaction) -> None:
        """All about Bot Frost"""

        await interaction.response.send_message(
            embed=buildEmbed(
                title="About Me",
                fields=[
                    dict(
                        name="History",
                        value="Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!",
                    ),
                    dict(
                        name="Source Code",
                        value=discordURLFormatter(
                            "GitHub", "https://www.github.com/refekt/Husker-Bot"
                        ),
                    ),
                    dict(name="Version", value=_version),
                    dict(
                        name="Hosting Location",
                        value=f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}",
                    ),
                    dict(
                        name="Hosting Status",
                        value="https://status.hyperexpert.com/",
                    ),
                    dict(
                        name="Latency",
                        value=f"{interaction.client.latency * 1000:.2f} ms",
                    ),
                    dict(
                        name="Username",
                        value=interaction.client.user.mention,
                    ),
                    dict(
                        name="Feeling generous?",
                        value=f"Check out `/donate` to help out the production and upkeep of the bot.",
                    ),
                ],
            )
        )

    @app_commands.command(
        name="donate", description="Contribute to the development of Bot Frost"
    )
    @app_commands.guilds(GUILD_PROD)
    async def donate(self, interaction: discord.Interaction) -> None:
        """Contribute to the development of Bot Frost"""

        await interaction.response.send_message(
            embed=buildEmbed(
                title="Donation Information",
                thumbnail="https://i.imgur.com/53GeCvm.png",
                fields=[
                    dict(
                        name="About",
                        value="I hate asking for donations; however, the bot has grown to the point where official server hosting is required. Server hosting provides 99% uptime and hardware performance I cannot provide with my own hardware. I will be paying for upgraded hosting but donations will help offset any costs.",
                    ),
                    dict(
                        name="Terms",
                        value="(1) Final discretion of donation usage is up to the creator(s). "
                        "(2) Making a donation to the product(s) and/or service(s) does not garner any control or authority over product(s) or service(s). "
                        "(3) No refunds. "
                        "(4) Monthly subscriptions can be terminated by either party at any time. "
                        "(5) These terms can be changed at any time. Please read before each donation. "
                        "(6) Clicking the donation link signifies your agreement to these terms.",
                    ),
                    dict(
                        name="Donation Link",
                        value=discordURLFormatter(
                            "click me",
                            "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url",
                        ),
                    ),
                ],
            )
        )

    @app_commands.command(
        name="commands", description="Lists all commands within the bot"
    )
    @app_commands.guilds(GUILD_PROD)
    async def commands(self, interaction: discord.Interaction) -> None:
        """Lists all commands within the bot"""

        await interaction.response.defer()

        app_cmds: dict[
            Union[discord.app_commands.Group, discord.app_commands.Command]
        ] = [
            bot_guild_command
            for bot_guild_command in interaction.client.tree._guild_commands.items()  # noqa
        ][
            0
        ][
            1
        ]
        # Don't judge me for the craziness above

        embed_fields_commands: list[dict] = []

        for cmd in app_cmds.items():
            cmd_name = cmd[0]
            cmd_command = cmd[1]
            if str(cmd_name).lower() == "smms":
                continue

            if type(cmd_command) == discord.app_commands.Command:
                embed_fields_commands.append(
                    dict(
                        name=str(cmd_name).capitalize(),
                        value=cmd_command.description
                        if cmd_command.description
                        else "TBD",
                    )
                )
            elif type(cmd) == discord.app_commands.Group:
                for sub_cmd in cmd_command.commands:
                    embed_fields_commands.append(
                        dict(
                            name=f"{str(cmd_name).title()} {sub_cmd.name.title()}",
                            value=sub_cmd.description if sub_cmd.description else "TBD",
                        )
                    )

        embed_fields_commands = sorted(embed_fields_commands, key=lambda x: x["name"])

        embeds: list[discord.Embed] = list()
        limit = 10  # Arbitary limit
        if len(embed_fields_commands) > limit:
            logger.info("Number of commands surprasses Discord embed field limitations")
            temp = []
            for i in range(0, len(embed_fields_commands), limit):
                temp.append(embed_fields_commands[i : i + limit])
            embeds = [
                buildEmbed(
                    title="Bot Frost Commands",
                    description=f"There are {len(embed_fields_commands)} commands",
                    fields=array,
                )
                for array in temp
            ]
        else:
            embeds.append(
                buildEmbed(
                    title="Bot Frost Commands",
                    description=f"There are {len(embed_fields_commands)} commands",
                    fields=embed_fields_commands,
                )
            )

        view = EmbedPaginatorView(
            embeds=embeds, original_message=await interaction.original_message()
        )

        await interaction.followup.send(embed=view.initial, view=view)

    @group_purge.command(
        name="bot", description="Purge the 100 most recent bot messages"
    )
    async def purge_bot(self, interaction: discord.Interaction) -> None:
        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )

        if not await self.confirm_purge(interaction):
            await interaction.edit_original_message(content="Purge declined", view=None)
            return

        await interaction.edit_original_message(content="Working...")

        msgs = await self.college_purge_messages(
            channel=interaction.channel, all_messages=False
        )

        await interaction.channel.delete_messages(msgs)
        await interaction.edit_original_message(
            content=f"Bulk delete of {len(msgs)} messages successful.", view=None
        )
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @group_purge.command(name="all", description="Purge the 100 most recent messages")
    async def purge_all(self, interaction: discord.Interaction) -> None:
        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )

        if not await self.confirm_purge(interaction):
            await interaction.edit_original_message(content="Purge declined", view=None)
            return

        await interaction.edit_original_message(content="Working...")

        msgs = await self.college_purge_messages(
            channel=interaction.channel, all_messages=True
        )

        await interaction.channel.delete_messages(msgs)
        await interaction.edit_original_message(
            content=f"Bulk delete of {len(msgs)} messages successful.", view=None
        )
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @app_commands.command(name="quit", description="Turn off Bot Frost")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(GUILD_PROD)
    async def quit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send(
            f"Goodbye for now! {interaction.user.mention} has turned me off!"
        )

        await interaction.client.close()

    @group_restart.command(name="bot", description="Restart the bot")
    async def bot(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "Bot will restart shortly!", ephemeral=True
        )

        assert "Windows" not in platform.platform(), CommandException(
            "Cannot run this command while hosted on Windows"
        )

        logger.info("Starting to update the changelog")
        bash_script_path = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.parent.resolve()}/changelog.sh"
        )
        logger.info(f"Opening bash script: {bash_script_path}")
        try:
            subprocess.run([bash_script_path], check=True)
        except subprocess.CalledProcessError as e:
            logger.exception(
                f"Status Code: {e.returncode}, Output: {e.output}", exc_info=True
            )
            pass

        logger.info("Starting to restart the bot")
        bash_script_path = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.parent.resolve()}/restart.sh"
        )
        logger.info(f"Opening bash script: {bash_script_path}")
        try:
            subprocess.run([bash_script_path], check=True)
        except subprocess.CalledProcessError as e:
            raise SSHException(f"Status Code: {e.returncode}, Output: {e.output}")

    @group_restart.command(name="twitter", description="Restart the twitter stream")
    async def twitter(self, interaction: discord.Interaction) -> None:
        logger.info("Restarting the twitter bot")
        start_twitter_stream(client=interaction.client)
        logger.info("Twitter stream restarted!")

    @group_submit.command(name="bug", description="Submit a bug")
    async def submit_bug(self, interaction: discord.Interaction) -> None:
        embed = buildEmbed(
            title="Bug Reporter",
            description=discordURLFormatter(
                "Submit a bug report here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=bug&template=bug_report.md&title=%5BBUG%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    @group_submit.command(name="feature", description="Submit a feature")
    async def submit_feature(self, interaction: discord.Interaction) -> None:
        embed = buildEmbed(
            title="Feature Request",
            description=discordURLFormatter(
                "Submit a feature request here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=request&template=feature_request.md&title=%5BREQUEST%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    async def proess_nebraska(
        self, interaction: discord.Interaction, who: discord.Member
    ) -> None:
        logger.info(f"Starting Nebraska for {who.name}#{who.discriminator}")

        assert who, UserInputException("You must include a user!")

        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True)

        role_timeout = interaction.guild.get_role(ROLE_TIME_OUT)
        try:
            await who.remove_roles(role_timeout)
        except (Forbidden, HTTPException) as e:
            logger.exception(f"Unable to remove the timeout role!\n{e}", exc_info=True)

        logger.info(f"Removed [{role_timeout}] role")

        previous_roles_raw = processMySQL(
            query=sqlRetrieveIowa, values=who.id, fetch="all"
        )

        processMySQL(query=sqlRemoveIowa, values=who.id)

        if previous_roles_raw is not None:
            previous_roles = previous_roles_raw[0]["previous_roles"].split(",")
            logger.info(f"Gathered all the roles to store")

            if previous_roles:
                for role in previous_roles:
                    try:
                        new_role = interaction.guild.get_role(int(role))
                        logger.info(f"Attempting to add [{new_role}] role...")
                        await who.add_roles(new_role, reason="Returning from Iowa")
                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                        discord.ext.commands.MissingPermissions,
                    ) as e:
                        logger.info(f"Unable to add role!\n{e}")
                        continue

                    logger.info(f"Added [{new_role}] role")

        embed = buildEmbed(
            title="Return to Nebraska",
            fields=[
                {
                    "name": "Welcome back!",
                    "value": f"[{who.mention}] is welcomed back to Nebraska!",
                },
                {
                    "name": "Welcomed by",
                    "value": interaction.user.mention,
                },
            ],
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed)
        else:
            await interaction.channel.send(embed=embed)

    @app_commands.command(name="iowa", description="Send someone to Iowa")
    @app_commands.describe(
        who="User to send to Iowa",
        reason="The reason why",
        duration="Number of seconds to send user to Iowa. 3600 = 1 hour, 86400 = 1 day",
    )
    @app_commands.guilds(GUILD_PROD)
    @app_commands.default_permissions(manage_messages=True)
    async def iowa(
        self,
        interaction: discord.Interaction,
        who: DISCORD_USER_TYPES,
        reason: str,
        duration: int = None,
    ) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Starting the Iowa command and banishing {who.name}#{who.discriminator}"
        )

        assert who, UserInputException("You must include a user!")
        assert reason, UserInputException("You must include a reason why!")

        role_timeout = interaction.guild.get_role(ROLE_TIME_OUT)
        channel_iowa = interaction.guild.get_channel(CHAN_IOWA)
        full_reason = (
            f"Time Out by {interaction.user.name}#{interaction.user.discriminator}: "
            + reason
        )

        previous_roles = [str(role.id) for role in who.roles[1:]]
        if previous_roles:
            previous_roles = ",".join(previous_roles)

        logger.info(f"Gathered all the roles to store")

        roles = who.roles
        for role in roles:
            try:
                await who.remove_roles(role, reason=full_reason)
                logger.info(f"Removed [{role}] role")
            except (discord.Forbidden, discord.HTTPException):
                continue

        try:
            await who.add_roles(role_timeout, reason=full_reason)
        except (discord.Forbidden, discord.HTTPException):
            logger.exception(
                f"Unable to add role to {who.name}#{who.discriminator}!", exc_info=True
            )

        logger.info(f"Added [{role_timeout}] role to {who.name}#{who.discriminator}")

        processMySQL(query=sqlInsertIowa, values=(who.id, full_reason, previous_roles))

        embed = buildEmbed(
            title="Banished to Iowa",
            fields=[
                {
                    "name": "Statement",
                    "value": f"[{who.mention}] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {role_timeout.mention} will be reapplied on rejoining the server."
                    + f"This will be reverted in {duration} seconds."
                    if duration is not None
                    else "",
                },
                {"name": "Reason", "value": full_reason, "inline": False},
            ],
        )

        await interaction.followup.send(embed=embed)
        await who.send(
            f"You have been moved to [ {channel_iowa.mention} ] for the following reason: {reason}."
            + f"This will be reverted in {duration} seconds."
            if duration is not None
            else ""
        )

        if duration is not None:
            await wait_and_run(
                duration=duration,
                func=self.proess_nebraska(interaction=interaction, who=who),
            )

        logger.info("Iowa command complete")

    @app_commands.command(name="nebraska", description="Bring someone back to Nebraska")
    @app_commands.describe(who="User to bring back to Nebraska")
    @app_commands.guilds(GUILD_PROD)
    @app_commands.default_permissions(manage_messages=True)
    async def nebraska(
        self,
        interaction: discord.Interaction,
        who: DISCORD_USER_TYPES,
    ) -> None:

        await self.proess_nebraska(interaction=interaction, who=who)

        logger.info("Nebraska command complete")

    @group_gameday.command(
        name="on",
        description="Turn game day mode on. Restricts access to server channels.",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def gameday_on(self, interaction: discord.Interaction) -> None:
        logger.info(f"Game Day: On")
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Processing!")
        await self.process_gameday(True, interaction.guild)
        await self.alert_gameday_channels(client=interaction.client, on=True)

    @group_gameday.command(
        name="off",
        description="Turn game day mode off. Restores access to server channels.",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def gameday_off(self, interaction: discord.Interaction) -> None:
        logger.info(f"Game Day: Off")
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Processing!")
        await self.process_gameday(False, interaction.guild)
        await self.alert_gameday_channels(client=interaction.client, on=False)

    @app_commands.command(name="smms", description="Tee hee")  # TODO Make hidden
    @app_commands.default_permissions(manage_messages=True)
    async def smms(
        self,
        interaction: discord.Interaction,
        destination: MammalChannels,
        message: str,
    ) -> None:
        assert message, CommandException("You cannot have a blank message!")

        await interaction.response.defer(ephemeral=True, thinking=True)

        chan = None
        if destination.name == "general":
            chan = await interaction.guild.fetch_channel(CHAN_GENERAL)
        elif destination.name == "recruiting":
            chan = await interaction.guild.fetch_channel(CHAN_RECRUITING)
        elif destination.name == "admin":
            chan = await interaction.guild.fetch_channel(CHAN_ADMIN)

        embed = buildEmbed(
            title="Secret Mammal Message System (SMMS)",
            description="These messages have no way to be verified to be accurate.",
            thumbnail="https://i.imgur.com/EGC1qNt.jpg",
            footer=BOT_FOOTER_SECRET,
            fields=[
                dict(
                    name="Back Channel Communication",
                    value=message,
                )
            ],
        )
        await chan.send(embed=embed)

        await interaction.followup.send(
            f"Back channel communication successfully sent to {chan.mention}!"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
