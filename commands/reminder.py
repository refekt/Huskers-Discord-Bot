import asyncio
import re
from datetime import datetime, timedelta

import discord
import nest_asyncio
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option

from objects.Thread import send_reminder
from utilities.constants import CHAN_BANNED
from utilities.constants import command_error
from utilities.constants import which_guild
from utilities.constants import DT_OBJ_FORMAT
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlRecordTasks
from utilities.constants import pretty_time_delta


class DateTimeStrings:
    day = "d"
    hour = "h"
    minute = "m"
    seconds = "s"


class ReminderCommands(commands.Cog):
    @cog_ext.cog_slash(
        name="remindme",
        description="Set a reminder",
        guild_ids=[which_guild()],
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
            raise command_error("You cannot input both a member and channel to remind.")
        elif who and not ctx.author == who:
            raise command_error("You cannot set reminders for anyone other than yourself!")
        elif channel in CHAN_BANNED:
            raise ValueError(f"Setting reminders in {channel.mention} is banned!")

        await ctx.defer()

        today = datetime.today()  # .astimezone(tz=TZ)

        def get_value(dt_item: str, from_when: str):

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

        days = get_value(DateTimeStrings.day, remind_when)
        hours = get_value(DateTimeStrings.hour, remind_when)
        minutes = get_value(DateTimeStrings.minute, remind_when)
        seconds = get_value(DateTimeStrings.seconds, remind_when)

        time_diff = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        min_timer_allowed = 5  # 60 * 5

        if time_diff.total_seconds() < min_timer_allowed:
            raise command_error(f"The num_seconds entered is too short! The minimum allowed timer is {min_timer_allowed} seconds.")

        try:
            raw_when = today + time_diff
        except ValueError:
            raise command_error("The num_seconds entered is too large!")

        duration = raw_when - today
        send_when = today + duration
        author = f"{ctx.author.name}#{ctx.author.discriminator}"
        is_open = 1

        if who:
            try:
                Process_MySQL(sqlRecordTasks, values=(str(who.id), message, str(send_when), is_open, author))
            except:
                raise command_error("Error submitting MySQL")

            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{who.mention}] in [{pretty_time_delta(duration.total_seconds())}]. The timer will go off at [{send_when.strftime('%x %X')}]."]
                ]
            )
        elif channel:
            try:
                Process_MySQL(sqlRecordTasks, values=(str(channel.id), message, str(send_when), is_open, author))
            except:
                raise command_error("Error submitting MySQL")

            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{channel.mention}] in [{pretty_time_delta(duration.total_seconds())}]. The timer will go off at [{send_when.strftime('%x %X')}]."]
                ]
            )
        else:
            try:
                Process_MySQL(sqlRecordTasks, values=(str(ctx.channel_id), message, str(send_when), is_open, author))
            except:
                raise command_error("Error submitting MySQL")

            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{ctx.channel.mention}] in [{pretty_time_delta(duration.total_seconds())}]. The timer will go off at [{send_when.strftime('%x %X')}]."]
                ]
            )

        await ctx.send(embed=embed)

        nest_asyncio.apply()
        asyncio.create_task(
            send_reminder(
                thread_name=str(who.id if who else channel.id if channel else ctx.author_id + duration.total_seconds()),
                num_seconds=duration.total_seconds(),
                destination=who if who else channel if channel else ctx.author,
                message=message,
                source=ctx.author,
                alert_when=str(send_when)
            )
        )
        embed = build_embed(
            title="Bot Frost Reminder",
            inline=False,
            fields=[
                ["Reminder created!", f"Reminder will be sent {send_when.strftime(DT_OBJ_FORMAT)}"],
                ["Destination", who.mention if who else channel.mention if channel else ctx.author.mention],
                ["Message", message]
            ]
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(ReminderCommands(bot))
