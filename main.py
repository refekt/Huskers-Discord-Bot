import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.all()

bot = commands.Bot(
    command_prefix="$",
    intents=intents
)


@bot.command()
async def hello(ctx):
    await ctx.send("Hello!")


bot.run("")
