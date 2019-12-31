from discord.ext import commands
import youtube_dl
import sys
from utils.consts import chan_radio_prod, chan_radio_test


class RadioBot():
    channel = None

    def __init__(self):
        if sys.argv[0] == "prod":
            self.channel = chan_radio_prod
        elif sys.argv[0] == "test":
            self.channel = chan_radio_test


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


print("### Radio Commands loaded!! ###")
