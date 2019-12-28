from discord.ext import commands

import discord
import asyncio
import re
import time
import youtube_dl

# Game == pressence


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
