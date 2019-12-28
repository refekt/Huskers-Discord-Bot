from discord.ext import commands


class BettingCommands(commands.Cog, name="Betting Commands"):
    pass


def setup(bot):
    bot.add_cog(BettingCommands(bot))


print("### Betting Commands loaded! ###")
