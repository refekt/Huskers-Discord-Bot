import asyncio
import re
from datetime import (
    datetime,
    timedelta
)

import discord
import nest_asyncio
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option

from objects.Thread import send_reminder
from utilities.constants import (
    CHAN_BANNED,
    CommandError,
    UserError,
    guild_id_list,
    pretty_time_delta
)
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlRecordTasks
)


class DateTimeStrings:
    day = "d"
    hour = "h"
    minute = "m"
    seconds = "s"


class ReminderCommands(commands.Cog):
    @cog_ext.cog_slash(
        name="remindme",
        description="Set a reminder",
        guild_ids=guild_id_list(),
        options=[
            create_option(
                name="remind_when",
                description="When to send the message",
                option_type=3,
                required=True
            ),
            create_option(
                name="message",
                description="The message to be sent",
                option_type=3,
                required=True
            ),
            create_option(
                name="who",
                description="Who to send the reminder to",
                option_type=6,
                required=False
            ),
            create_option(
                name="channel",
                description="Which channel to send the reminder to",
                option_type=7,
                required=False
            )
        ]
    )
    async def _remindme(self, ctx: SlashContext, remind_when: str, message: str, who: discord.member = None, channel: discord.TextChannel = None):
        if who and channel:
            raise UserError("You cannot input both a member and channel to remind.")
        elif who and not ctx.author == who:
            raise UserError("You cannot set reminders for anyone other than yourself!")
        elif channel in CHAN_BANNED:
            raise ValueError(f"Setting reminders in {channel.mention} is banned!")

        await ctx.defer()

        today = datetime.today()

        def convert_dt_value(dt_item: str, from_when: str):

            if dt_item in from_when:
                raw = from_when.split(dt_item)[0]
                if raw.isnumeric():
                    return int(raw)
                else:
                    try:
                        findall = re.findall(r"\D", raw)[-1]
                        return int(raw[raw.find(findall) + 1:])
                    except:
                        return 0
            else:
                return 0

        days = convert_dt_value(DateTimeStrings.day, remind_when)
        hours = convert_dt_value(DateTimeStrings.hour, remind_when)
        minutes = convert_dt_value(DateTimeStrings.minute, remind_when)
        seconds = convert_dt_value(DateTimeStrings.seconds, remind_when)

        time_diff = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        min_timer_allowed = 5  # 60 * 5

        if time_diff.total_seconds() < min_timer_allowed:
            raise UserError(f"The num_seconds entered is too short! The minimum allowed timer is {min_timer_allowed} seconds.")

        try:
            raw_when = today + time_diff
        except ValueError:
            raise UserError("The num_seconds entered is too large!")

        duration = raw_when - today
        send_when = today + duration
        mysql_author = f"{ctx.author.name}#{ctx.author.discriminator}"
        is_open = 1

        if who:
            destination = who
        elif channel:
            destination = channel
        else:
            destination = ctx.channel

        try:
            Process_MySQL(sqlRecordTasks, values=(str(destination.id), message, str(send_when), is_open, mysql_author))
            destination = ctx.channel
        except:
            raise CommandError("Error submitting MySQL")

        nest_asyncio.apply()
        asyncio.create_task(
            send_reminder(
                num_seconds=duration.total_seconds(),
                destination=destination,
                message=message,
                source=ctx.author,
                alert_when=str(send_when)
            )
        )

        embed = build_embed(
            title="Bot Frost Reminders",
            description=f"Setting a timer for [{destination.mention}] in [{pretty_time_delta(duration.total_seconds())}]. The timer will go off at [{send_when.strftime('%x %X')}].",
            inline=False,
            fields=[
                ["Author", ctx.author.mention],
                ["Message", message]
            ]
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ReminderCommands(bot))
