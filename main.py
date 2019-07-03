import discord
from discord.ext import commands
import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
from discord.utils import get
import random
import re
import importlib
import sys
import uuid

prefix = "$"
bot = commands.Bot(command_prefix=prefix)

# add a command for stocks to stonks
# add iowasux command, reactions

def loadFongBombs():
    # The intent for this function is to web scrape data from 247Sports and eventually display Crystal Ball updates from Wiltfong.
    print("Loading Fong Bomgs!")

    url='https://247sports.com/User/Steve%20Wiltfong/Predictions/?PlayerInstitution.PrimaryPlayerSport.Sport=Football&PlayerInstitution.PrimaryPlayerSport.Recruitment.Year=2020'

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    print("\n",soup.find_all("li"),"\n")

    '''for i in range(0,len(soup.find_all("li","target"))+1):
        one_li_tag = soup.find_all("li","target")[0]
        link = one_li_tag['class']

        print(link)'''

    print("Fong Bombs loaded!")

def main():
    # loadFongBombs()
    print('nada')

if __name__ == "__main__":
    main()

@bot.event
async def on_ready():
    print("Logged in.")

@bot.event
async def on_message(message):
    # Change "stocks" to "stonks" because Isms
    '''if not message.author.bot and "stock" in message.content.lower():
        llamaString = message.content.replace('Stock', 'Stonk')
        newString = re.compile("stock", re.IGNORECASE)
    await message.channel.send(message.channel, newString.sub('stonk', llamaString))'''

    await bot.process_commands(message)

@bot.command(pass_context=True)
async def iowasux(ctx):
    #WORK IN PROGRESS
    # I cannot figure out how to add reactions. add_reaction does not seem to populate.
    await ctx.send("You're god damn right they do!", emoji = bot.get_emoji(":iowasux:"))

f = open("../token.txt","r")
bot.run(f.readline())