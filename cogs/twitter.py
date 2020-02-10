from discord.ext import commands


class TwitterCommands(commands.Cog, name="Twitter Commands"):
    pass


def setup(bot):
    bot.add_cog(TwitterCommands(bot))