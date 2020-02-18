from discord.ext import commands


class ChatBot(commands.Cog, name="ChatBot Commands"):
    pass


def setup(bot):
    bot.add_cog(ChatBot(bot))
