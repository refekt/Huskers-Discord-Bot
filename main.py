import discord
from discord.ext import commands
from discord.utils import get
import requests
import re
from bs4 import BeautifulSoup

prefix = "$"
bot = commands.Bot(command_prefix=prefix)

# add a command for stocks to stonks
# add iowasux command, reactions

"""def loadFongBombs():
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

    print("Fong Bombs loaded!")"""

def main():
    print("*")

if __name__ == "__main__":
    main()

@bot.event
async def on_ready():
    print("Logged in.")

@bot.event
async def on_message(message):
    """ Commands processed as messages are entered """

    # Good bot, bad bot
    if not message.author.bot and "good bot" in message.content.lower():
        await message.channel.send("OwO thanks")
    elif not message.author.bot and "bad bot" in message.content.lower():
        embed = discord.Embed(title="I'm a bad, bad bot")
        embed.set_image(url='https://i.imgur.com/qDuOctd.gif')
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

@bot.command(pass_context=True)
async def iowasux(ctx):
    """ Iowa Sucks """

    # Need to add reactions
    await ctx.send("You're god damn right they do!")

@bot.command(pass_context=True)
async def stonk(ctx):
    """ Isms hates stocks """
    await ctx.send("Stonk!")

@bot.command(pass_context=True)
async def potatoes(ctx):
    """ Potatoes are love; potatoes are life """
    embed = discord.Embed(title="Po-Tay-Toes")
    embed.set_image(url='https://i.imgur.com/Fzw6Gbh.gif')
    await ctx.send(embed=embed)

# Retrieve the Discord Bot Token
f = open("../token.txt","r")
bot.run(f.readline())