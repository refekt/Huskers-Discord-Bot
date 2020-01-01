from discord.ext import commands

from utils.client import client
from utils.consts import _global_rate, _global_per, _global_type
from utils.consts import chan_radio_test, chan_radio_prod
from utils.consts import role_admin_prod, role_admin_test, role_mod_prod
from utils.misc import on_prod_server


def radio_channel():
    return client.get_channel(id=chan_radio_prod if on_prod_server() else chan_radio_test)


voice_client = None


class RadioCommands(commands.Cog):

    @commands.group()
    @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    @commands.cooldown(rate=_global_rate, per=_global_per, type=_global_type)
    async def radio(self, ctx):
        return

    @radio.command()
    async def start(self, ctx):
        channel = radio_channel()
        global voice_client
        voice_client = await channel.connect()

    @radio.command()
    async def stop(self, ctx):
        global voice_client
        await voice_client.disconnect()


def setup(bot):
    bot.add_cog(RadioCommands(bot))