from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
import nest_asyncio
import asyncio
from utilities.constants import which_guild
from objects.Thread import send_reminder
from datetime import datetime, timedelta


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=[which_guild()]
    )
    async def _test(self, ctx: SlashContext):
        await ctx.defer()
        nest_asyncio.apply()

        alert = datetime.now() + timedelta(seconds=10)
        asyncio.create_task(
            send_reminder(
                thread=1,
                destination=ctx.author,
                num_seconds=3,
                message="Testing",
                alert_when=alert,
                source=ctx.author
            )
        )
        await ctx.send("Test started")



def setup(bot):
    bot.add_cog(TestCommand(bot))
