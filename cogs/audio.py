from discord import VoiceChannel
from discord.ext import commands
from utils.client import client
from utils.consts import _global_rate, _global_per, _global_type
from utils.consts import role_admin_prod, role_admin_test, role_mod_prod
import sys
from utils.consts import chan_radio_test, chan_radio_prod

if sys.argv[1] == "prod":
    channel = client.get_channel(id=chan_radio_prod)
elif sys.argv[1] == "test":
    channel = client.get_channel(id=chan_radio_test)

channel_connection = None


class RadioCommands(commands.Cog):

    @commands.group()
    @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    @commands.cooldown(rate=_global_rate, per=_global_per, type=_global_type)
    async def radio(self, ctx):
        return

    @radio.command()
    async def start(self, ctx):
        global channel_connection
        channel_connection = await channel.connect()

    @radio.command()
    async def stop(self, ctx):
        if channel_connection.is_connect():
            await channel_connection.disconnect()


def setup(bot):
    bot.add_cog(RadioCommands(bot))