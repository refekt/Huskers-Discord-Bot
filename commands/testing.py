from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.context import SlashContext

from utilities.constants import which_guild
from utilities.embed import build_embed


class TestCommand(commands.Cog):
    @cog_ext.cog_slash(
        name="test",
        description="Test command",
        guild_ids=[which_guild()]
    )
    async def _test(self, ctx: SlashContext):
        embed = build_embed(
            # title="test",
            # description="test",
            # footer="sdfdsafsadfasfasfsafasdfasf"
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TestCommand(bot))
