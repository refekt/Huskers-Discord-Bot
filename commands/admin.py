import logging
import pathlib
import platform
import socket
from datetime import datetime

import discord.ext.commands
import paramiko
from discord.ext import commands
from paramiko.ssh_exception import (
    BadHostKeyException,
    AuthenticationException,
    SSHException,
)

from helpers.constants import (
    CHAN_BOTLOGS,
    DISCORD_USER_TYPES,
    SSH_HOST,
    SSH_USERNAME,
    SSH_PASSWORD,
)
from helpers.embed import buildEmbed
from helpers.misc import discordURLFormatter
from objects.Exceptions import UserInputException, CommandException

logger = logging.getLogger(__name__)


class AdminCog(commands.Cog, name="Admin Commands"):
    def __init__(self, client) -> None:
        self.client = client

    @commands.command()
    async def about(self, ctx: discord.ext.commands.Context):
        """All about Bot Frost"""
        import platform

        await ctx.send(
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

    @commands.command()
    async def donate(self, ctx: discord.ext.commands.Context):
        """Donate to the cause"""

        await ctx.send(
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

    @commands.command()  # TODO
    async def commands(self, ctx: discord.ext.commands.Context):
        ...

    @commands.group()
    async def purge(self, ctx: discord.ext.commands.Context):  # Bot, All
        """Deletes up to 100 bot messages"""

        assert ctx.subcommand_passed, UserInputException(
            "A subcommmand must be passed."
        )
        assert ctx.message.channel.id == CHAN_BOTLOGS, UserInputException(
            "This command is not authorized in this channel."
        )

    @purge.command()
    async def bot(self, ctx: discord.ext.commands.Context):
        msgs = []
        max_age = datetime.now() - datetime.timedelta(
            days=13, hours=23, minutes=59
        )  # Discord only lets you delete 14 day old messages

        try:
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age and message.author.bot:
                    msgs.append(message)

            await ctx.message.channel.delete_messages(msgs)
        except discord.ClientException:
            logger.warning("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            logger.error("Missing permissions.")
        except discord.HTTPException:
            logger.error(
                "Deleting messages failed. Bulk messages possibly include messages over 14 days old."
            )

        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @purge.command()
    async def all(self, ctx: discord.ext.commands.Context):
        # TODO Add a "double check" button to make sure you want to delete

        msgs = []
        max_age = datetime.now() - datetime.timedelta(
            days=13, hours=23, minutes=59
        )  # Discord only lets you delete 14 day old messages

        try:
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age:
                    msgs.append(message)

            await ctx.message.channel.delete_messages(msgs)
        except discord.ClientException:
            logger.warning("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            logger.error("Missing permissions.")
        except discord.HTTPException:
            logger.error(
                "Deleting messages failed. Bulk messages possibly include messages over 14 days old."
            )

        logger.info(f"Bulk delete of {len(msgs)} messages successful.")

    @purge.command()
    async def user(
        self,
        ctx: discord.ext.commands.Context,
        who: DISCORD_USER_TYPES,
    ):
        # TODO Add a "double check" button to make sure you want to delete
        assert who is None, UserInputException("You must provide a user/member.")

        msgs = []
        max_age = datetime.now() - datetime.timedelta(
            days=13, hours=23, minutes=59
        )  # Discord only lets you delete 14 day old messages

        try:
            async for message in ctx.message.channel.history(limit=100):
                if message.created_at >= max_age and message.author.id == who.id:
                    msgs.append(message)

            await ctx.message.channel.delete_messages(msgs)
        except discord.ClientException:
            logger.warning("Cannot delete more than 100 messages at a time.")
        except discord.Forbidden:
            logger.error("Missing permissions.")
        except discord.HTTPException:
            logger.error(
                "Deleting messages failed. Bulk messages possibly include messages over 14 days old."
            )

        logger.info(f"Bulk delete of {len(msgs)} {who.mention}'s messages successful.")

    @commands.command()
    async def quit(self, ctx: discord.ext.commands.Context):
        await ctx.send(f"Goodbye for now! {ctx.author.mention} has turned me off!")
        await self.client.logout()
        logger.info(f"User `{ctx.author}` turned off the bot.")

    @commands.command()
    async def restart(self, ctx: discord.ext.commands.Context):
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

        await ctx.send("Bot restart complete!")

    @commands.group()
    async def submit(self, ctx: discord.ext.commands.Context):
        assert ctx.subcommand_passed, UserInputException(
            "A subcommmand must be passed."
        )

    @submit.command()
    async def bug(self, ctx: discord.ext.commands.Context):
        embed = buildEmbed(
            title="Bug Reporter",
            description=discordURLFormatter(
                "Submit a bug report here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=bug&template=bug_report.md&title=%5BBUG%5D+",
            ),
        )
        await ctx.send(embed=embed)

    @submit.command()
    async def feature(self, ctx: discord.ext.commands.Context):
        embed = buildEmbed(
            title="Feature Request",
            description=discordURLFormatter(
                "Submit a feature request here",
                "https://github.com/refekt/Bot-Frost/issues/new?assignees=refekt&labels=request&template=feature_request.md&title=%5BREQUEST%5D+",
            ),
        )
        await ctx.send(embed=embed)

    @commands.command()  # TODO
    async def iowa(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()  # TODO
    async def nebraska(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()  # TODO
    async def gameday(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()  # TODO
    async def smms(self, ctx: discord.ext.commands.Context):
        ...


def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))
