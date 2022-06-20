import asyncio
from datetime import datetime, timedelta
from typing import Optional, Union

import discord.ext.commands
from discord import app_commands
from discord.ext import commands

from helpers.constants import GUILD_PROD, TZ, DT_OBJ_FORMAT
from helpers.embed import buildEmbed
from helpers.mysql import processMySQL, sqlRecordReminder, sqlUpdateReminder
from objects.Exceptions import ReminderException
from objects.Logger import discordLogger
from objects.Thread import (
    wait_and_run,
    convertDateTimeString,
    DateTimeChars,
    prettifyTimeDateValue,
)

logger = discordLogger(__name__)

__all__ = [
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
    ):
        self.duration = duration
        self.author = author
        self.destination = destination
        self.message = message
        self.remind_who = remind_who
        self.missed_reminder = missed_reminder

    async def run(self):
        logger.info(f"Sleeping for {self.duration.total_seconds():,} seconds")
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

        logger.info("Self destructing MissedReminder")
        del self


async def send_reminder(
    author: Union[discord.Member, str],
    destination: discord.TextChannel,
    message: str,
    remind_who: Union[discord.Member, int, None] = None,
    missed_reminder: bool = False,
):
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

    embed = buildEmbed(
        title=f"Reminder Message for {remind_who.name}#{remind_who.discriminator}"
        if isinstance(remind_who, discord.Member)
        else "Reminder Message",
        author=author.display_name
        if isinstance(author, discord.Member)
        else author,  # A str may be passed from loading reminders/tasks
        icon_url=author.display_avatar if isinstance(author, discord.Member) else None,
        description=f"Missed reminder! {message}" if missed_reminder else message,
        footer=f"Reminder was created on {datetime.datetime.now(tz=TZ).strftime(DT_OBJ_FORMAT)}",
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
    @app_commands.guilds(GUILD_PROD)
    async def remind_me(
        self,
        interaction: discord.Interaction,
        destination: discord.TextChannel,
        message: str,
        duration: str,
        remind_who: Optional[discord.Member] = None,
    ) -> None:
        logger.info("Creating a reminder!")
        if interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        assert True in [
            dt.__str__() in duration for dt in DateTimeChars
        ], ReminderException(
            "The duration must be in the proper format! E.g.; 1h30m30s or 1d30m."
        )

        dt_duration: datetime.timedelta = convertDateTimeString(duration)

        await interaction.followup.send(
            f"Reminder set and will be sent in {prettifyTimeDateValue(dt_duration.total_seconds())}",
            ephemeral=True,
        )

        processMySQL(
            query=sqlRecordReminder,
            values=(
                destination.id if remind_who is None else remind_who.id,
                message,
                dt_duration + datetime.datetime.now(),
                1,  # True
                f"{interaction.user.name}#{interaction.user.discriminator}",
            ),
        )

        logger.info(
            f"Sleeping for {prettifyTimeDateValue(dt_duration.total_seconds())}"
        )
        await wait_and_run(
            duration=dt_duration,
            func=send_reminder(
                author=interaction.user,
                destination=destination,
                message=message,
                remind_who=remind_who,
            ),
        )

        logger.info("Updating MySQL to set to reminder is_opent o False")
        print(
            0,  # False
            destination.id if remind_who is None else remind_who.id,
            message,
            interaction.user.id,
        )
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
