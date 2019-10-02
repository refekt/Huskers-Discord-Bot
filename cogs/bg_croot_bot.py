from discord.ext import tasks
from cogs.croot_bot import *
import asyncpg


class BackgroundRefresh(commands.Cog, name="Background Refresh"):
    def __init__(self, bot):
        self.bot = bot
        self.data = []
        self.bg_cb_refresh.add_exception_type(asyncpg.PostgresConnectionError)
        self.bg_cb_refresh.start()

    def cog_unload(self):
        self.bg_cb_refresh.stop()

    @tasks.loop(hours=4)
    async def bg_cb_refresh(self):
        print("Starting background task for Crystal Ball refreshing...")
        await check_last_run()

    @bg_cb_refresh.before_loop
    async def before_bg_cb_refresh(self):
        print("Waiting to start background task for Crystal Ball refreshing...")
        await self.bot.wait_until_ready()

    @bg_cb_refresh.after_loop
    async def after_bg_cb_refresh(self):
        print("Stopped background task for Crystal Ball refreshing...")
        pass  # Place holder


def setup(bot):
    bot.add_cog(BackgroundRefresh(bot))