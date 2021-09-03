from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext

from utilities.constants import guild_id_list


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ {message}")


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=guild_id_list()
    )
    async def _test(self, ctx: SlashContext):
        pass


def setup(bot):
    bot.add_cog(TestCommand(bot))
