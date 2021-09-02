from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext

from objects.Thread import twitter_stream
from utilities.constants import guild_id_list


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=guild_id_list()
    )
    async def _test(self, ctx: SlashContext):
        await twitter_stream(ctx.channel)


def setup(bot):
    bot.add_cog(TestCommand(bot))
