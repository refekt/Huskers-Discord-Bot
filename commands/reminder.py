from datetime import datetime, timedelta

import asyncio
import discord
import nest_asyncio
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_commands import create_option

from utilities.constants import CHAN_BANNED
from utilities.constants import command_error
from utilities.constants import which_guild
from utilities.mysql import Process_MySQL, sqlRecordTasks
from objects.Thread import send_reminder
from utilities.embed import build_embed


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
                name="destination",
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
            import re

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

        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

        min_timer_allowed = 60 * 5

        if delta.total_seconds() < min_timer_allowed:
            raise command_error(f"The num_seconds entered is too short! The minimum allowed timer is {min_timer_allowed} seconds.")

        try:
            raw_when = today + delta
        except ValueError:
            raise command_error("The num_seconds entered is too large!")

        duration = raw_when - today
        alert_when = today + duration
        author = f"{ctx.author.name}#{ctx.author.discriminator}"

        if who:
            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{who.mention}] in [{duration.total_seconds()}] seconds. The timer will go off at [{alert_when.strftime('%x %X')}]."]
                ]
            )
            await ctx.send(embed=embed)
            Process_MySQL(sqlRecordTasks, values=(who.id, message, str(alert_when), 1, author))
        elif channel:
            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{channel.mention}] in [{duration.total_seconds()}] seconds. The timer will go off at [{alert_when.strftime('%x %X')}]."]
                ]
            )
            await ctx.send(embed=embed)
            Process_MySQL(sqlRecordTasks, values=(channel.id, message, str(alert_when), 1, author))
        else:
            embed = build_embed(
                title="Bot Frost Reminders",
                inline=False,
                fields=[
                    ["Reminder created!", f"Setting a timer for [{ctx.channel.mention}] in [{duration.total_seconds()}] seconds. The timer will go off at [{alert_when.strftime('%x %X')}]."]
                ]
            )
            await ctx.send(embed=embed)
            Process_MySQL(sqlRecordTasks, values=(ctx.channel.id, message, str(alert_when), 1, author))

        nest_asyncio.apply()
        asyncio.create_task(
            send_reminder(
                thread=1,
                num_seconds=duration.total_seconds(),
                destination=who,
                message=message,
                source=ctx.author,
                alert_when=str(alert_when)
            )
        )


def setup(bot):
    bot.add_cog(ReminderCommands(bot))
