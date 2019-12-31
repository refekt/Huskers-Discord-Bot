import sys

# import youtube_dl
from discord.channel import VoiceChannel
from discord.ext import commands

from utils.client import client
from utils.consts import chan_radio_prod, chan_radio_test


def voice_channel():
    if sys.argv[1] == "prod":
        return chan_radio_prod
    elif sys.argv[1] == "test":
        return chan_radio_test


class RadioBot:
    channel_id = None
    channel = VoiceChannel
    voice_client = None

    def __init__(self, channel):
        self.channel_id = channel
        self.channel = client.get_channel(id=self.channel_id)

    async def connect(self):
        self.voice_client = await self.channel.connect()

    async def disconnect(self):
        await self.voice_client.disconnect()


class RadioCommands(commands.Cog, name="Radio Commands"):
    @commands.group()
    async def radio(self, ctx):
        pass

    @radio.command()
    async def join(self, ctx):
        r = RadioBot(channel=voice_channel())
        await r.connect()

    @radio.command()
    async def leave(self, ctx):
        r = RadioBot(channel=voice_channel())
        await r.disconnect()


def setup(bot):
    bot.add_cog(RadioCommands(bot))


print("### Radio Commands loaded!! ###")
