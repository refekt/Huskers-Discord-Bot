import logging
import pathlib
import platform
import socket
from datetime import datetime, timedelta
from typing import Any

import discord.ext.commands
import paramiko
from discord import app_commands, Forbidden, HTTPException
from discord.ext import commands
from paramiko.ssh_exception import (
    BadHostKeyException,
    AuthenticationException,
    SSHException,
)

from __version__ import _version
from helpers.constants import (
    DISCORD_USER_TYPES,
    SSH_HOST,
    SSH_USERNAME,
    SSH_PASSWORD,
    GUILD_PROD,
    ROLE_TIME_OUT,
    CHAN_IOWA,
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter
from helpers.mysql import processMySQL, sqlInsertIowa, sqlRetrieveIowa, sqlRemoveIowa
from objects.Exceptions import CommandException, UserInputException

logger = logging.getLogger(__name__)


async def validate_purge(interaction: discord.Interaction):
    ...


async def college_purge_messages(channel: Any, all_messages: bool = False):
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
        logger.warning("Cannot delete more than 100 messages at a time.")
    except discord.Forbidden:
        logger.error("Missing permissions.")
    except discord.HTTPException:
        logger.error(
            "Deleting messages failed. Bulk messages possibly include messages over 14 days old."
        )

    return msgs


class AdminCog(commands.Cog, name="Admin Commands"):
    def __init__(self, client: discord.ext.commands.Bot) -> None:
        self.client: discord.ext.commands.Bot = client
        super().__init__()

    group_purge = app_commands.Group(
        name="purge",
        description="TBD",
        default_permissions=discord.Permissions(manage_messages=True),
    )
    group_submit = app_commands.Group(
        name="submit",
        description="TBD",
    )

    @app_commands.command(name="about")
    async def about(self, interaction: discord.Interaction) -> None:
        """All about Bot Frost"""
        import platform

        await interaction.response.send_message(
            embed=buildEmbed(
                title="About Me",
                inline=False,
                fields=[
                    {
                        "name": "History",
                        "value": "Bot Frost was created and developed by [/u/refekt](https://reddit.com/u/refekt) and [/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assisted with the creation greatly!",
                        "inline": False,
                    },
                    {
                        "name": "Source Code",
                        # "value": "[GitHub](https://www.github.com/refekt/Husker-Bot)",
                        "value": discordURLFormatter(
                            "GitHub", "https://www.github.com/refekt/Husker-Bot"
                        ),
                        "inline": False,
                    },
                    {"name": "Version", "value": _version, "inline": False},
                    {
                        "name": "Hosting Location",
                        "value": f"{'Local Machine' if 'Windows' in platform.platform() else 'Virtual Private Server'}",
                        "inline": False,
                    },
                    {
                        "name": "Hosting Status",
                        "value": "https://status.hyperexpert.com/",
                        "inline": False,
                    },
                    {
                        "name": "Latency",
                        "value": f"{self.client.latency * 1000:.2f} ms",
                        "inline": False,
                    },
                    {
                        "name": "Username",
                        "value": self.client.user.mention,
                        "inline": False,
                    },
                    {
                        "name": "Feeling generous?",
                        "value": f"Check out `/donate` to help out the production and upkeep of the bot.",
                        "inline": False,
                    },
                ],
            )
        )

    @app_commands.command(name="donate")
    async def donate(self, interaction: discord.Interaction) -> None:
        """Donate to the cause"""

        await interaction.response.send_message(
            embed=buildEmbed(
                title="Donation Information",
                inline=False,
                thumbnail="https://i.imgur.com/53GeCvm.png",
                fields=[
                    {
                        "name": "About",
                        "value": "I hate asking for donations; however, the bot has grown to the point where official server hosting is required. Server hosting provides 99% uptime and hardware performance I cannot provide with my own hardware. I will be paying for upgraded hosting but donations will help offset any costs.",
                        "inline": False,
                    },
                    {
                        "name": "Terms",
                        "value": "(1) Final discretion of donation usage is up to the creator(s). "
                        "(2) Making a donation to the product(s) and/or service(s) does not garner any control or authority over product(s) or service(s). "
                        "(3) No refunds. "
                        "(4) Monthly subscriptions can be terminated by either party at any time. "
                        "(5) These terms can be changed at any time. Please read before each donation. "
                        "(6) Clicking the donation link signifies your agreement to these terms.",
                        "inline": False,
                    },
                    {
                        "name": "Donation Link",
                        # "value": "[Click Me](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url)",
                        "value": discordURLFormatter(
                            "click me",
                            "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=refekt%40gmail.com&currency_code=USD&source=url",
                        ),
                        "inline": False,
                    },
                ],
            )
        )

    @app_commands.command(name="commands")
    async def commands(self, interaction: discord.Interaction) -> None:
        """Lists all commands within the bot"""
        embed_fields_commands = [
            dict(
                name=cmd.name,
                value=cmd.description if cmd.description else "TBD",
                inline=False,
            )
            for cmd in self.client.commands
        ]
        embed = buildEmbed(title="Bot Commands", fields=embed_fields_commands)
        await interaction.response.send_message(embed=embed)

    @group_purge.command(name="bot")
    async def purge_bot(self, interaction: discord.Interaction) -> None:
        # TODO Add a "double check" button to make sure you want to delete
        await validate_purge(interaction)

        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )
        await interaction.response.defer(ephemeral=True)
        msgs = await college_purge_messages(
            channel=interaction.channel, all_messages=False
        )
        await interaction.channel.delete_messages(msgs)
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")
        await interaction.followup.send(
            f"Bulk delete of {len(msgs)} messages successful.", ephemeral=True
        )

    @group_purge.command(name="all")
    async def purge_all(self, interaction: discord.Interaction) -> None:
        # TODO Add a "double check" button to make sure you want to delete
        await validate_purge(interaction)

        assert type(interaction.channel) is discord.TextChannel, CommandException(
            "Unable to run this command outside text channels."
        )
        await interaction.response.defer(ephemeral=True)
        msgs = await college_purge_messages(
            channel=interaction.channel, all_messages=True
        )
        await interaction.channel.delete_messages(msgs)
        logger.info(f"Bulk delete of {len(msgs)} messages successful.")
        await interaction.followup.send(
            f"Bulk delete of {len(msgs)} messages successful.", ephemeral=True
        )

    @app_commands.command(name="quit")
    @app_commands.default_permissions(manage_messages=True)
    async def quit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Goodbye for now! {interaction.user.mention} has turned me off!"
        )
        await self.client.close()
        logger.info(
            f"User {interaction.user.name}#{interaction.user.discriminator} turned off the bot."
        )

    @app_commands.command(name="restart")  # TODO Test on Linux
    @app_commands.default_permissions(manage_messages=True)
    async def restart(self, interaction: discord.Interaction) -> None:
        interaction.response.defer(ephemeral=True, thinking=True)

        assert "Windows" not in platform.platform(), CommandException(
            "Cannot run this command while hosted on Windows"
        )

        logger.info("Restarting the bot via SSH")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info("SSH Client established")

        try:
            client.connect(
                hostname=SSH_HOST, username=SSH_USERNAME, password=SSH_PASSWORD
            )
        except (
            BadHostKeyException,
            AuthenticationException,
            SSHException,
            socket.error,
        ):
            logger.error("SSH Client was unable to connect to host")
            raise CommandException("Unable to restart the bot!")

        logger.info("SSH Client connected to host")

        # Update change log
        bash_script_path = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.parent.resolve()}/changelog.sh"
        )
        bash_script = open(bash_script_path).read()

        stdin, stdout, stderr = client.exec_command(bash_script)
        logger.info(stdout.read().decode())

        err = stderr.read().decode()
        assert err is None, CommandException(err)

        # Restart
        bash_script_path = pathlib.PurePosixPath(
            f"{pathlib.Path(__file__).parent.parent.parent.resolve()}/restart.sh"
        )
        bash_script = open(bash_script_path).read()

        stdin, stdout, stderr = client.exec_command(bash_script)
        logger.info(stdout.read().decode())

        err = stderr.read().decode()
        assert err is None, CommandException(err)

        client.close()
        logger.info("SSH Client is closed.")

        await interaction.channel.send("Bot restart complete!")

    @group_submit.command()
    async def bug(self, interaction: discord.Interaction) -> None:
        embed = buildEmbed(
            title="Bug Reporter",
            description=discordURLFormatter(
                "Submit a bug report here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=bug&template=bug_report.md&title=%5BBUG%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    @group_submit.command()
    async def feature(self, interaction: discord.Interaction) -> None:
        embed = buildEmbed(
            title="Feature Request",
            description=discordURLFormatter(
                "Submit a feature request here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=request&template=feature_request.md&title=%5BREQUEST%5D+",
            ),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="iowa")  # TODO
    @app_commands.default_permissions(manage_messages=True)
    async def iowa(
        self,
        interaction: discord.Interaction,
        who: DISCORD_USER_TYPES,
        reason: str,
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
            raise CommandException(
                f"Unable to add role to {who.name}#{who.discriminator}!"
            )

        logger.info(f"Added [{role_timeout}] role to {who.name}#{who.discriminator}")

        processMySQL(query=sqlInsertIowa, values=(who.id, full_reason, previous_roles))

        embed = buildEmbed(
            title="Banished to Iowa",
            fields=[
                {
                    "name": "Statement",
                    "value": f"[{who.mention}] has had all roles removed and been sent to Iowa. Their User ID has been recorded and {role_timeout.mention} will be reapplied on rejoining the server.",
                    "inline": False,
                },
                {"name": "Reason", "value": full_reason, "inline": False},
            ],
        )

        await interaction.followup.send(embed=embed)
        await who.send(
            f"You have been moved to [ {channel_iowa.mention} ] for the following reason: {reason}."
        )
        logger.info("Iowa command complete")

    @app_commands.command(name="nebraska")  # TODO
    @app_commands.default_permissions(manage_messages=True)
    async def nebraska(
        self,
        interaction: discord.Interaction,
        who: DISCORD_USER_TYPES,
    ) -> None:
        assert who, UserInputException("You must include a user!")

        await interaction.response.defer(thinking=True)

        role_timeout = interaction.guild.get_role(ROLE_TIME_OUT)
        try:
            await who.remove_roles(role_timeout)
        except (Forbidden, HTTPException) as e:
            raise CommandException(f"Unable to remove the timeout role!\n{e}")

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
                    "inline": False,
                },
                {
                    "name": "Welcomed by",
                    "value": interaction.user.mention,
                    "inline": False,
                },
            ],
        )
        await interaction.followup.send(embed=embed)

        logger.info("Nebraska command complete")

    @app_commands.command(name="gameday")  # TODO
    @app_commands.default_permissions(manage_messages=True)
    async def gameday(self, interaction: discord.Interaction) -> None:
        ...

    @app_commands.command(name="smms")  # TODO
    @app_commands.default_permissions(manage_messages=True)
    async def smms(self, interaction: discord.Interaction) -> None:
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
