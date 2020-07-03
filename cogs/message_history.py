from datetime import datetime

import discord
from discord.ext import commands

from utils.client import client
from utils.consts import GUILD_PROD, GUILD_TEST
from utils.consts import PROD_BOT_MEMBER, TEST_BOT_MEMBER
from utils.consts import ROLE_ADMIN_TEST, ROLE_ADMIN_PROD
from utils.mysql import process_MySQL, sqlRecordStatsManual


class HistoryCommands(commands.Cog, name="History Commands"):
    @commands.command(hidden=True)
    @commands.has_any_role(ROLE_ADMIN_PROD, ROLE_ADMIN_TEST)
    async def genhis(self, ctx):
        history = []
        guild = member = None

        guild = client.get_guild(id=GUILD_PROD)

        if guild is None:
            guild = client.get_guild(id=GUILD_TEST)

        member = guild.get_member(PROD_BOT_MEMBER)

        if member is None:
            member = guild.get_member(TEST_BOT_MEMBER)

        async def compile_history(chan: discord.TextChannel, limit=9999):
            history_raw = await chan.history(limit=limit, after=datetime(year=2020, month=5, day=1)).flatten()
            history_new = []

            for entry in history_raw:
                history_new.append([
                    str(entry.author).encode("ascii", "ignore").decode("ascii"),
                    str(entry.channel).encode("ascii", "ignore").decode("ascii"),
                    str(entry.created_at.strftime("%Y-%m-%d %H:%M:%S")).encode("ascii", "ignore").decode("ascii")
                ])

            del history_raw

            return history_new

        for channel in guild.channels:
            perms = channel.permissions_for(member)

            if not perms.read_message_history:
                continue

            if channel.type == discord.ChannelType.text:
                print(f"Grabbing history for {channel.name}...")
                history.extend(await compile_history(channel))
                print("Done!")
            else:
                continue

        for entry in history:
            print(repr(entry))
            process_MySQL(query=sqlRecordStatsManual, values=entry)


def setup(bot):
    bot.add_cog(HistoryCommands(bot))
