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

from helpers.constants import GUILD_PROD


class TextCog(commands.Cog, name="Text Commands"):
    @commands.command()
    async def eightball(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def markov(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def police(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def possum(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def survey(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def urbandictionary(self, ctx: discord.interactions.Interaction):
        ...

    @commands.command()
    async def weather(self, ctx: discord.interactions.Interaction):
        ...


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TextCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
