# TODO
# * About
# * Commands
# * Donate
# * Gameday (on, off)
# * Iowa
# * Nebraska
# * Purge (everything, bot)
# * Quit
# * Restart
# * Roles (hype)
# * SMMS
# * Submit (bug, feature)
# TODO
import discord.ext.commands
from discord.ext import commands


class AdminCog(commands.Cog, name="Admin Commands"):
    def __init__(self, client) -> None:
        self.client = client

    @commands.command()
    async def about(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def donate(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def commands(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def purge(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def quit(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def restart(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def submit(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def iowa(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def nebraska(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def gameday(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def smms(self, ctx: discord.ext.commands.Context):
        ...


def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))
