import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD, TZ, DT_OBJ_FORMAT, DEBUGGING_CODE
from helpers.embed import buildEmbed
from helpers.mysql import processMySQL, sqlRecordReminder, sqlUpdateReminder
from objects.Exceptions import ReminderException
from objects.Logger import discordLogger
from objects.Thread import (
    DateTimeChars,
    background_run_function,
    convertDateTimeString,
    prettifyTimeDateValue,
)

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = [
    "MissedReminder",
    "send_reminder",
]


class MissedReminder:
    def __init__(
        self,
        duration: timedelta,
        author: Union[discord.Member, str],
        destination: discord.TextChannel,
        message: str,
        remind_who: Union[discord.Member, int, None] = None,
        missed_reminder: bool = False,
    ) -> None:
        self.duration: timedelta = duration
        self.author: Union[discord.Member, str] = author
        self.destination: discord.TextChannel = destination
        self.message: str = message
        self.remind_who: Union[discord.Member, int, None] = remind_who
        self.missed_reminder: bool = missed_reminder

    async def run(self) -> None:
        logger.debug(f"Sleeping for {self.duration.total_seconds():,} seconds")
        await asyncio.sleep(self.duration.total_seconds())
        logger.info("Sleep complete. Sending reminder!")

        await send_reminder(
            author=self.author,
            destination=self.destination,
            message=self.message,
            remind_who=self.remind_who,
            missed_reminder=self.missed_reminder,
        )

        processMySQL(
            query=sqlUpdateReminder,
            values=(
                0,  # False
                self.destination,
                self.message,
                self.author,
            ),
        )

        logger.debug("Self destructing MissedReminder")
        del self


async def send_reminder(
    author: Union[discord.Member, str],
    destination: discord.TextChannel,
    message: str,
    remind_who: Union[discord.Member, int, None] = None,
    missed_reminder: bool = False,
) -> None:
    if missed_reminder:
        processMySQL(
            query=sqlUpdateReminder,
            values=(
                0,  # False
                destination,
                message,
                author,
            ),
        )

    embed: discord.Embed = buildEmbed(
        title=f"Reminder Message for {remind_who.name}#{remind_who.discriminator}"
        if isinstance(remind_who, discord.Member)
        else "Reminder Message",
        author=author.display_name
        if isinstance(author, discord.Member)
        else author,  # A str may be passed from loading reminders/tasks
        icon_url=author.display_avatar if isinstance(author, discord.Member) else None,
        description=f"Missed reminder! {message}" if missed_reminder else message,
        footer=f"Reminder was created on {datetime.now(tz=TZ).strftime(DT_OBJ_FORMAT)}",
    )
    await destination.send(
        embed=embed, content=f"Paging {remind_who.mention}" if remind_who else ""
    )


class ReminderCog(commands.Cog, name="Reminder Commands"):
    @app_commands.command(name="remind-me", description="TBD")
    @app_commands.describe(
        destination="The channel the message will go to.",
        message="The message to be sent.",
        duration="Duration in ##d##h##m##s format. E.g.; 30m, 1d6h, 6h30s.",
        remind_who="The member to ping",
    )
    @app_commands.guilds(discord.Object(id=GUILD_PROD))
    async def remind_me(
        self,
        interaction: discord.Interaction,
        destination: discord.TextChannel,
        message: str,
        duration: str,
        remind_who: Optional[discord.Member] = None,
    ) -> None:
        logger.info("Creating a reminder!")
        await interaction.response.defer(ephemeral=True)

        assert True in [
            dt.__str__() in duration for dt in DateTimeChars
        ], ReminderException(
            "The duration must be in the proper format! E.g.; 1h30m30s or 1d30m."
        )

        dt_duration: timedelta = convertDateTimeString(duration)

        await interaction.followup.send(
            f"Reminder set and will be sent in {prettifyTimeDateValue(dt_duration.total_seconds())}",
            ephemeral=True,
        )

        logger.debug("Creating MySQL entry for reminder")
        processMySQL(
            query=sqlRecordReminder,
            values=(
                destination.id if remind_who is None else remind_who.id,
                message,
                dt_duration + datetime.now(),
                1,  # True
                f"{interaction.user.name}#{interaction.user.discriminator}",
            ),
        )

        logger.info(
            f"Sleeping for {prettifyTimeDateValue(dt_duration.total_seconds())}"
        )
        await background_run_function(
            func=send_reminder(
                author=interaction.user,
                destination=destination,
                message=message,
                remind_who=remind_who,
            ),
            duration=dt_duration,
            loop=interaction.client.loop,
        )

        logger.debug("Updating MySQL to set to reminder is_open to False")
        processMySQL(
            query=sqlUpdateReminder,
            values=(
                0,  # False
                destination.id if remind_who is None else remind_who.id,
                message,
                f"{interaction.user.name}#{interaction.user.discriminator}",
            ),
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReminderCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
