import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

prefix = "$"
bot = commands.Bot(command_prefix=prefix)

# add a command for stocks to stonks
# add iowasux command, reactions

"""def loadFongBombs():
    # The intent for this function is to web scrape data from 247Sports and eventually display Crystal Ball updates from Wiltfong.
    url='https://247sports.com/User/Steve%20Wiltfong/Predictions/'
    r = requests.get(url)
    print(r.content)"""

def main():
    #loadFongBombs()
    print("")

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

"""@bot.command(pass_context=True)
async def loadFong(ctx):
    # The intent for this function is to web scrape data from 247Sports and eventually display Crystal Ball updates from Wiltfong.
    # Currently receiving a 500 Internal Server Error each pull
    url = 'https://247sports.com/User/Steve%20Wiltfong/Predictions/?PlayerInstitution.PrimaryPlayerSport.Sport=Football&PlayerInstitution.PrimaryPlayerSport.Recruitment.Year=2020'
    page_response = requests.get(url, timeout=5)
    page_content = BeautifulSoup(page_response.content, "html.parser")
    print(page_content.contents)"""

# Retrieve the Discord Bot Token
f = open("../token.txt","r")
bot.run(f.readline())