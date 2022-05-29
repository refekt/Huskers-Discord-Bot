import logging
import pathlib
import platform
import socket
from datetime import datetime, timedelta
from typing import Any

import discord.ext.commands
import paramiko
from discord import app_commands
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
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter
from objects.Exceptions import UserInputException, CommandException

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

    group_purge = app_commands.Group(name="purge", description="TBD")
    group_submit = app_commands.Group(name="submit", description="TBD")

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
    async def quit(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Goodbye for now! {interaction.user.mention} has turned me off!"
        )
        await self.client.close()
        logger.info(
            f"User {interaction.user.name}#{interaction.user.discriminator} turned off the bot."
        )

    @app_commands.command(name="restart")  # TODO Test on Linux
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
    async def iowa(self, interaction: discord.Interaction) -> None:
        ...

    @app_commands.command(name="nebraska")  # TODO
    async def nebraska(self, interaction: discord.Interaction) -> None:
        ...

    @app_commands.command(name="gameday")  # TODO
    async def gameday(self, interaction: discord.Interaction) -> None:
        ...

    @app_commands.command(name="smms")  # TODO
    async def smms(self, interaction: discord.Interaction) -> None:
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AdminCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
