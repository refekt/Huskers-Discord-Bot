import requests
from discord.ext import commands
import discord


class CrootBot(commands.Cog, name="Croot Bot"):
    def __init__(self, bot):
        self.bot = bot
        pass