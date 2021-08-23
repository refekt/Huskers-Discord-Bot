from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import SlashMessage
from utilities.constants import guild_id_list
from utilities.embed import build_embed
from objects.Thread import start_twitter_stream, TaskThread

print(f"Guild ID List: {type(guild_id_list())} {guild_id_list()}")


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
