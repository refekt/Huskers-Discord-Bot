import sys

from discord.ext import commands
from discord.channel import VoiceChannel
from utils.client import client
import discord
from utils.consts import chan_radio_prod, chan_radio_test
from utils.consts import guild_test, guild_prod


class DiscordRadio:
    channel = VoiceChannel

    def __init__(self, channel):
        self.channel = channel


r = DiscordRadio(chan_radio_test)
guild = discord.get_guild(id=guild_test)

print(r)


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
