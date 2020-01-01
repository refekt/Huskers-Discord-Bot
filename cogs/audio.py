from discord import VoiceChannel
from discord.ext import commands
from utils.client import client
from utils.consts import _global_rate, _global_per, _global_type
from utils.consts import role_admin_prod, role_admin_test, role_mod_prod


class RadioHelper():
    def __init__(self, channel: VoiceChannel):
        self.bot = client
        self.channel = channel
        self.started = False
    pass


class RadioCommands(commands.Cog):

    @commands.group()
    @commands.has_any_role(role_admin_test, role_admin_prod, role_mod_prod)
    @commands.cooldown(rate=_global_rate, per=_global_per, type=_global_type)
    async def radio(self, ctx):
        return

    @radio.command()
    async def join(self, ctx):
        return

    @radio.command()
    async def leaev(self, ctx):
        return


def setup(bot):
    bot.add_cog(RadioCommands(bot))