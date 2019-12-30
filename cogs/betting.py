from discord.ext import commands

from utils.consts import _global_per
from utils.consts import _global_rate


class BetCommands(commands.Cog, name="Betting Commands"):
    @commands.group()
    @commands.cooldown(rate=_global_rate, per=_global_per, type=commands.BucketType.user)
    async def bet(self, ctx):
        """ Allows users to place bets for Husker games."""

    @bet.command(aliases=["a", ])
    async def all(self, ctx, *, team=None):
        """Show all the bets for the current or provided opponent."""

    @bet.command(aliases=["win", "w", ])
    async def winners(self, ctx, *, team):
        """Show the winners for the current or provided opponent."""

    @bet.command(aliases=["lb", ])
    async def leaderboard(self, ctx):
        """Shows the leaderboard for the season."""

    @bet.command(aliases=["s", ])
    async def show(self, ctx, *, team=None):
        """Shows the current or provided opponent placed bet(s)."""

    @bet.command(aliases=["line", "l", ])
    async def lines(self, ctx, *, team=None):
        """Shows the current or provided opponent lines."""

    @bet.command(hidden=True)
    @commands.has_any_role(606301197426753536, 440639061191950336, 443805741111836693)
    async def scores(self, ctx, score, oppo_score, *, team):
        """ Update the database """


def setup(bot):
    bot.add_cog(BetCommands(bot))
