import discord
from discord.ext import commands

# import youtube_dl

# Game == pressence
#
# if not discord.opus.is_loaded():
#     # the 'opus' library here is opus.dll on windows or libopus.so on linux in the current directory you should replace this with the location the opus library is located in.
#     discord.opus.load_opus("libopus-0")


class RadioCommands(commands.Cog, name="Radio Commands"):
    @commands.group()
    async def radio(self, ctx):
        pass

    @radio.command()
    async def join(self, ctx):
        pass

    @radio.command()
    async def leave(self, ctx):
        pass


def setup(bot):
    bot.add_cog(RadioCommands(bot))


print("### Radio Commands loaded! ###")
