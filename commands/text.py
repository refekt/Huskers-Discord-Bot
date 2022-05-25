# TODO
# * Eightball
# * Markov
# * Police
# * Possumdroppings
# * Survey
# * Urbandictionary
# * Vote
# * Weather
# TODO


import discord.ext.commands
from discord.ext import commands


class TextCog(commands.Cog, name="Text Commands"):
    @commands.command()
    async def eightball(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def markov(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def police(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def possum(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def survey(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def urbandictionary(self, ctx: discord.ext.commands.Context):
        ...

    @commands.command()
    async def weather(self, ctx: discord.ext.commands.Context):
        ...


def setup(bot: commands.Bot):
    bot.add_cog(TextCog(bot))
