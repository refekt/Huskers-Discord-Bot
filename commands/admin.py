import asyncio
import json
import logging
import pathlib
import platform
import subprocess
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Union, Optional, Generator

import discord.ext.commands
import requests
from discord import app_commands, Forbidden, HTTPException, InvalidData, NotFound
from discord.app_commands import Group, Command
from discord.ext import commands

from __version__ import _version
from helpers.constants import (
    BOT_FOOTER_SECRET,
    CAT_GAMEDAY,
    CAT_GENERAL,
    CHAN_ADMIN,
    CHAN_ANNOUNCEMENT,
    CHAN_DISCUSSION_LIVE,
    CHAN_DISCUSSION_STREAMING,
    CHAN_GENERAL,
    CHAN_HYPE_GROUP,
    CHAN_IOWA,
    CHAN_RECRUITING,
    DEBUGGING_CODE,
    DT_GITHUB_API,
    DT_GITHUB_API_DISPLAY,
    GUILD_PROD,
    ROLE_ANNOUNCEMENT,
    ROLE_EVERYONE_PROD,
    ROLE_TIME_OUT,
    TZ,
    WINDOWS_PATH,
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter, general_locked
from helpers.mysql import processMySQL, sqlInsertIowa, sqlRetrieveIowa, sqlRemoveIowa
from objects.Client import start_twitter_stream
from objects.Exceptions import CommandException, UserInputException, SSHException
from objects.Logger import discordLogger
from objects.Paginator import EmbedPaginatorView
from objects.Thread import (
    background_run_function,
    prettifyTimeDateValue,
    convertIowaDuration,
    prettifyLongTimeDateValue,
)
from objects.Timers import IowaDuration

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)


class ConfirmButtons(discord.ui.View):
    def __init__(self) -> None:
        super().__init__()
        self.value: Optional[bool] = None

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey)
    async def cancel(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        self.value = False
        self.stop()


class AdminCog(commands.Cog, name="Admin Commands"):
    class MammalChannels(Enum):
        general = 1
        recruiting = 2
        admin = 3

    group_purge: app_commands.Group = app_commands.Group(
        name="purge",
        description="Purge messages from channel",
        default_permissions=discord.Permissions(administrator=True),
        guild_ids=[GUILD_PROD],
    )
    group_gameday: app_commands.Group = app_commands.Group(
        name="gameday",
        description="Turn game day mode on or off",
        default_permissions=discord.Permissions(manage_messages=True),
        guild_ids=[GUILD_PROD],
    )
    group_restart: app_commands.Group = app_commands.Group(
        name="restart",
        description="Restart elements of the bot",
        default_permissions=discord.Permissions(manage_messages=True),
        guild_ids=[GUILD_PROD],
    )
    group_log: app_commands.Group = app_commands.Group(
        name="get-log",
        description="Get bot logs",
        default_permissions=discord.Permissions(administrator=True),
        guild_ids=[GUILD_PROD],
    )

    # noinspection PyMethodMayBeStatic
    async def alert_gameday_channels(
        self, client: Union[discord.ext.commands.Bot, discord.Client], on: bool
    ) -> None:
        chan_general: discord.TextChannel = await client.fetch_channel(CHAN_GENERAL)
        chan_live: discord.TextChannel = await client.fetch_channel(
            CHAN_DISCUSSION_LIVE
        )
        chan_streaming: discord.TextChannel = await client.fetch_channel(
            CHAN_DISCUSSION_STREAMING
        )

        if on:
            embed: discord.Embed = buildEmbed(
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

            await chan_live.send(embed=embed)
            await chan_streaming.send(embed=embed)
            await chan_general.send(embed=embed)

            # TODO Setup a background task that can be turned off
            while general_locked:
                await asyncio.sleep(60 * 10)
                await chan_general.send(embed=embed)
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

    # noinspection PyMethodMayBeStatic
    async def process_gameday(self, mode: bool, guild: discord.Guild) -> None:
        gameday_category: discord.CategoryChannel = guild.get_channel(CAT_GAMEDAY)
        general_category: discord.CategoryChannel = guild.get_channel(CAT_GENERAL)
        everyone: discord.Role = guild.get_role(ROLE_EVERYONE_PROD)

        logger.info(f"Creating permissions to be [{mode}]")

        perms_text: discord.PermissionOverwrite = discord.PermissionOverwrite()

        perms_text.view_channel = mode  # noqa
        perms_text.send_messages = mode  # noqa
        perms_text.read_messages = mode  # noqa

        perms_text_opposite: discord.PermissionOverwrite = discord.PermissionOverwrite()
        perms_text_opposite.send_messages = not mode  # noqa

        perms_voice: discord.PermissionOverwrite = discord.PermissionOverwrite()
        perms_voice.view_channel = mode  # noqa
        perms_voice.connect = mode  # noqa
        perms_voice.speak = mode  # noqa

        logger.info(f"Permissions created")

        for channel in general_category.channels:

            if channel.id in CHAN_HYPE_GROUP:
                continue

            try:
                logger.info(
                    f"Attempting to changes permissions for [{channel.name.encode('utf-8', 'replace')}] to [{not mode}]"
                )
                if channel.type == discord.ChannelType.text:
                    await channel.set_permissions(
                        everyone, overwrite=perms_text_opposite
                    )
            except:  # noqa
                logger.info(
                    f"Unable to change permissions for [{channel.name.encode('utf-8', 'replace')}] to [{not mode}]"
                )
                continue

            logger.info(
                f"Changed permissions for [{channel.name.encode('utf-8', 'replace')}] to [{not mode}]"
            )

        for channel in gameday_category.channels:
            try:
                logger.info(
                    f"Attempting to changes permissions for [{channel}] to [{mode}]"
                )

                if channel.type == discord.ChannelType.text:
                    await channel.set_permissions(everyone, overwrite=perms_text)
                elif channel.type == discord.ChannelType.voice:
                    await channel.set_permissions(everyone, overwrite=perms_voice)

                    # Disconnects embers from voice
                    for member in channel.members:
                        try:
                            await member.move_to(channel=None)
                        except (Forbidden, HTTPException, TypeError):
                            logger.warning(
                                f"Unable to disconnect {member.name}#{member.discriminator}"
                            )
                            continue
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
        msgs: list[discord.Message] = []
        max_age: datetime = datetime.now() - timedelta(
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

        view: ConfirmButtons = ConfirmButtons()
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
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def about(self, interaction: discord.Interaction) -> None:
        """All about Bot Frost"""

        github_api_url: str = "https://api.github.com/repos/refekt/Bot-Frost"
        github_commits_api_url: str = (
            "https://api.github.com/repos/refekt/Bot-Frost/stats/contributors"
        )
        github_response: requests.Response = requests.get(url=github_api_url)
        github_json: dict = json.loads(github_response.text)

        created_on: datetime = datetime.strptime(
            github_json.get("created_at", "UNK"), DT_GITHUB_API
        ).astimezone(tz=TZ)
        updated_on: datetime = datetime.strptime(
            github_json.get("updated_at", "UNK"), DT_GITHUB_API
        ).astimezone(tz=TZ)
        pushed_on: datetime = datetime.strptime(
            github_json.get("pushed_at", "UNK"), DT_GITHUB_API
        ).astimezone(tz=TZ)

        await interaction.response.send_message(
            embed=buildEmbed(
                title="About Me",
                fields=[
                    dict(
                        name="History",
                        value="Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!",
                    ),
                    dict(
                        name="GitHub Information",
                        value=f"Created On: {created_on.strftime(DT_GITHUB_API_DISPLAY)}\n"
                        f"Updated On: {updated_on.strftime(DT_GITHUB_API_DISPLAY)}\n"
                        f"Pushed On: {pushed_on.strftime(DT_GITHUB_API_DISPLAY)}\n"
                        f"Age: {prettifyLongTimeDateValue(datetime.now().astimezone(tz=TZ), created_on)}\n",
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
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
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
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def commands(self, interaction: discord.Interaction) -> None:
        """Lists all commands within the bot"""

        await interaction.response.defer(ephemeral=True)

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

        embed_fields_commands: list[dict[str, str]] = []

        def commandHasPerms(
            command: Union[discord.app_commands.Command, discord.app_commands.Group]
        ) -> bool:
            if command.default_permissions is None:
                return True

            if (
                command.default_permissions.administrator
                or command.default_permissions.manage_messages
            ) and not interaction.user.resolved_permissions.manage_messages:
                return False
            else:
                return True

        for cmd in app_cmds.items():
            cmd_name: Union[Group, Command] = cmd[0]
            cmd_command: Union[Group, Command] = cmd[1]
            if str(cmd_name).lower() == "smms":
                continue

            if type(cmd_command) == discord.app_commands.Command and commandHasPerms(
                cmd_command
            ):
                embed_fields_commands.append(
                    dict(
                        name=str(cmd_name).capitalize(),
                        value=cmd_command.description
                        if cmd_command.description
                        else "TBD",
                    )
                )
            elif type(cmd_command) == discord.app_commands.Group and commandHasPerms(
                cmd_command
            ):
                for sub_cmd in cmd_command.commands:
                    if not commandHasPerms(sub_cmd):
                        continue

                    embed_fields_commands.append(
                        dict(
                            name=f"{str(cmd_name).title()} {sub_cmd.name.title()}",
                            value=sub_cmd.description if sub_cmd.description else "TBD",
                        )
                    )

        embed_fields_commands = sorted(embed_fields_commands, key=lambda x: x["name"])

        embeds: list[discord.Embed] = list()
        limit: int = 10  # Arbitary limit
        if len(embed_fields_commands) > limit:
            logger.info("Number of commands surpasses Discord embed field limitations")
            temp: list = []
            for i in range(0, len(embed_fields_commands), limit):
                temp.append(embed_fields_commands[i : i + limit])
            embeds: list[discord.Embed] = [
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

        view: EmbedPaginatorView = EmbedPaginatorView(
            embeds=embeds, original_message=await interaction.original_response()
        )

        await interaction.followup.send(embed=view.initial, view=view)

    @group_purge.command(
        name="bot", description="Purge the 100 most recent bot messages"
    )
    async def purge_bot(self, interaction: discord.Interaction) -> None:
        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )

        if interaction.response.is_done():  # Trying to fix "Unknown interaction" errors
            await interaction.response.defer(ephemeral=True)

        if not await self.confirm_purge(interaction):
            await interaction.edit_original_response(
                content="Purge declined", view=None
            )
            return

        await interaction.edit_original_response(content="Working...")

        msgs: list[discord.Message] = await self.college_purge_messages(
            channel=interaction.channel, all_messages=False
        )

        await interaction.channel.delete_messages(msgs)
        await interaction.edit_original_response(
            content=f"Bulk delete of {len(msgs)} messages successful.", view=None
        )
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @group_purge.command(name="all", description="Purge the 100 most recent messages")
    async def purge_all(self, interaction: discord.Interaction) -> None:
        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )

        if not await self.confirm_purge(interaction):
            await interaction.edit_original_response(
                content="Purge declined", view=None
            )
            return

        await interaction.edit_original_response(content="Working...")

        msgs: list[discord.Message] = await self.college_purge_messages(
            channel=interaction.channel, all_messages=True
        )

        await interaction.channel.delete_messages(msgs)
        await interaction.edit_original_response(
            content=f"Bulk delete of {len(msgs)} messages successful.", view=None
        )
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @app_commands.command(name="quit", description="Turn off Bot Frost")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def quit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        await interaction.followup.send(
            f"So long suckers! {interaction.user.mention} has fired me after a 9-win season!"
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
        bash_script_path: pathlib.PurePosixPath = pathlib.PurePosixPath(
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
        await interaction.response.defer(ephemeral=True)
        await start_twitter_stream(client=interaction.client)
        await interaction.followup.send("Twitter stream has been restarted!")
        logger.info("Twitter stream restarted!")

    async def proess_nebraska(  # noqa
        self, interaction: discord.Interaction, who: discord.Member
    ) -> None:
        logger.info(f"Starting Nebraska for {who.name}#{who.discriminator}")

        assert who, UserInputException("You must include a user!")

        if not interaction.response.is_done():
            await interaction.response.defer(thinking=True)

        role_timeout: discord.Role = interaction.guild.get_role(ROLE_TIME_OUT)
        try:
            await who.remove_roles(role_timeout)
        except (Forbidden, HTTPException) as e:
            logger.exception(f"Unable to remove the timeout role!\n{e}", exc_info=True)

        logger.info(f"Removed [{role_timeout}] role")

        previous_roles_raw: Union[dict, list[dict, ...], None] = processMySQL(
            query=sqlRetrieveIowa, values=str(who.id), fetch="all"
        )

        processMySQL(query=sqlRemoveIowa, values=str(who.id))

        if previous_roles_raw is not None:
            previous_roles: str = previous_roles_raw[0]["previous_roles"].split(",")
            logger.info(f"Gathered all the roles to store")

            if previous_roles:
                for role in previous_roles:
                    try:
                        new_role: discord.Role = interaction.guild.get_role(int(role))
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

        embed: discord.Embed = buildEmbed(
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
        duration="How long you want the Iowa command to apply.",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    @app_commands.default_permissions(manage_messages=True)
    async def iowa(
        self,
        interaction: discord.Interaction,
        who: Union[discord.Member, discord.User],
        reason: str,
        duration: IowaDuration = None,
    ) -> None:
        await interaction.response.defer(thinking=True)

        logger.info(
            f"Starting the Iowa command and banishing {who.name}#{who.discriminator}"
        )

        assert who, UserInputException("You must include a user!")
        assert reason, UserInputException("You must include a reason why!")

        if duration:
            # assert True in [
            #     dt.__str__() in duration for dt in DateTimeChars
            # ], UserInputException(
            #     "The duration must be in the proper format! E.g.; 1h30m30s or 1d30m."
            # )

            dt_duration: Optional[timedelta] = convertIowaDuration(duration)
        else:
            dt_duration = None

        role_timeout: discord.Role = interaction.guild.get_role(ROLE_TIME_OUT)
        channel_iowa: discord.TextChannel = interaction.guild.get_channel(CHAN_IOWA)
        full_reason: str = (
            f"Time Out by {interaction.user.name}#{interaction.user.discriminator}: "
            + reason
        )

        previous_roles: Union[list[str], str] = [str(role.id) for role in who.roles[1:]]
        if len(previous_roles):
            previous_roles = ",".join(previous_roles)
        else:
            previous_roles = ""

        logger.info(f"Gathered all the roles to store")

        roles: list[discord.Role] = who.roles
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
        logger.debug("Saved old roles roles to MySQL database")

        statement_str: str = f"[{who.mention}] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {role_timeout.mention} will be reapplied on rejoining the server."
        message_str: str = f"You have been moved to [ {channel_iowa.mention} ] for the following reason: {reason}."

        if duration:
            statement_str += f" This will be reverted in {prettifyTimeDateValue(dt_duration.seconds)}."
            message_str += f" This will be reverted in {prettifyTimeDateValue(dt_duration.seconds)}."

        embed: discord.Embed = buildEmbed(
            title="Banished to Iowa",
            fields=[
                dict(name="Statement", value=statement_str),
                dict(name="Reason", value=full_reason),
            ],
        )

        await interaction.followup.send(embed=embed)
        try:
            await who.send(message_str)
        except (HTTPException, Forbidden, ValueError, TypeError):
            pass

        if duration is not None:
            await background_run_function(
                func=self.proess_nebraska(interaction=interaction, who=who),
                duration=dt_duration,
                loop=interaction.client.loop,
            )

        logger.info("Iowa command complete")

    @app_commands.command(name="nebraska", description="Bring someone back to Nebraska")
    @app_commands.describe(who="User to bring back to Nebraska")
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    @app_commands.default_permissions(manage_messages=True)
    async def nebraska(
        self,
        interaction: discord.Interaction,
        who: Union[discord.Member, discord.User],
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

    @app_commands.command(name="smms", description="Tee hee")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def smms(
        self,
        interaction: discord.Interaction,
        destination: MammalChannels,
        message: str,
    ) -> None:
        assert message, CommandException("You cannot have a blank message!")

        await interaction.response.defer(ephemeral=True, thinking=True)

        chan: Optional[discord.TextChannel] = None
        if destination.name == "general":
            chan = await interaction.guild.fetch_channel(CHAN_GENERAL)
        elif destination.name == "recruiting":
            chan = await interaction.guild.fetch_channel(CHAN_RECRUITING)
        elif destination.name == "admin":
            chan = await interaction.guild.fetch_channel(CHAN_ADMIN)

        embed: discord.Embed = buildEmbed(
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

    @group_log.command(name="bot", description="Send last few lines of bot.log")
    async def get_log(self, interaction: discord.Interaction) -> None:
        logger.debug("Grabbing and sending bot.log")

        await interaction.response.defer(ephemeral=True)

        path_log: pathlib.PurePosixPath = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/logs/bot.log"
        )

        file: discord.File = discord.File(
            path_log,
            filename="bot.txt",
            description=f"Bot's log as of {datetime.now(tz=TZ)}",
        )

        await interaction.user.send(content="!", file=file)
        await interaction.followup.send(
            f"Log sent in a DM! {interaction.client.user.mention}\nLog path: {path_log}"
        )

        logger.debug("Sent bot.log")

    @group_log.command(
        name="twitter", description="Send last few lines of tweepy.client.log"
    )
    async def get_log(self, interaction: discord.Interaction) -> None:
        logger.debug("Grabbing and sending bot.log")

        await interaction.response.defer(ephemeral=True)

        path_log: pathlib.PurePosixPath = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/logs/tweepy.client.log"
        )

        file: discord.File = discord.File(
            path_log,
            filename="tweepy.txt",
            description=f"Bot's log as of {datetime.now(tz=TZ)}",
        )

        await interaction.user.send(content="!", file=file)
        await interaction.followup.send(
            f"Log sent in a DM! {interaction.client.user.mention}\nLog path: {path_log}"
        )

        logger.debug("Sent bot.log")

    @group_log.command(name="download", description="Download the logs")
    async def get_download(self, interaction: discord.Interaction) -> None:
        remote_path: pathlib.PurePosixPath = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.resolve()}/logs/log.log"
        )
        remote_folder: Generator = pathlib.Path(remote_path.parent).glob("**/*")
        remote_files: list[Union[pathlib.WindowsPath, pathlib.PosixPath]] = [
            item for item in remote_folder if item.is_file()
        ]

        local_path: pathlib.Path = pathlib.Path(WINDOWS_PATH)
        local_folder: Generator = local_path.glob("**/*")
        local_files: list[Union[pathlib.WindowsPath]] = [
            item for item in local_folder if item.is_file()
        ]

        for index, local_file in enumerate(local_files):
            try:
                with open(local_file, "w") as log_file:
                    contents: str = remote_files[index].read_text()
                    local_file.write_text(contents)
                    logger.info(f"Downlaoded and copied {local_file}")
            except IOError:
                logger.info(f"Cannot download {local_file}")
                continue

    @app_commands.command(
        name="server-announcement",
        description="Send an announcement out ot the server.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def server_announcement(
        self, interaction: discord.Interaction, title: str, message: str
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        try:
            channel_announcement: discord.TextChannel = (
                await interaction.client.fetch_channel(CHAN_ANNOUNCEMENT)
            )
        except (InvalidData, HTTPException, NotFound, Forbidden):
            return

        embed = buildEmbed(
            title="Server Announcement", fields=[dict(name=title, value=message)]
        )

        role_announcement: Optional[discord.Role] = interaction.guild.get_role(
            ROLE_ANNOUNCEMENT
        )

        if role_announcement:
            await channel_announcement.send(
                content=f"{role_announcement.mention}", embed=embed
            )
        else:
            await channel_announcement.send(content=f"@Announcements", embed=embed)

        await interaction.followup.send(
            f"Announcement has been sent to {channel_announcement.mention}"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
