import discord
from discord.ext import commands
# from discord.utils import get
import requests
from bs4 import BeautifulSoup

prefix = "$"
bot = commands.Bot(command_prefix=prefix)


@bot.event
async def on_ready():
    print("Logged in. Discord.py version is:",discord.__version__)


'''@bot.event
async def on_reaction_add(reaction, user):
    await reaction.message.channel.send('{} has added {} to the messge: {}'.format(user.name, reaction.emoji, reaction.message.content))'''


@bot.event
async def on_message(message):
    """ Commands processed as messages are entered """

    if not message.author.bot:
        # Good bot, bad bot
        if "good bot" in message.content.lower():
            await message.channel.send("OwO thanks")
        elif "bad bot" in message.content.lower():
            embed = discord.Embed(title="I'm a bad, bad bot")
            embed.set_image(url='https://i.imgur.com/qDuOctd.gif')
            await message.channel.send(embed=embed)
        # Husker Bot hates Isms
        if "isms" in message.content.lower():
            await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and make shut up for fake internet points. I’m glad he’s gone.")

    await bot.process_commands(message)


'''@bot.command(pass_context=True)
async def clearBotChat(ctx, amount=100):
    channel = ctx.message.channel
    messages = []
    async for message in bot.logs_from(channel, int(limit=amount)):
        messages.append(message)
    await bot.delete_messages(messages)
    await bot.say('Messages deleted')'''


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


@bot.command(pass_context=True)
async def loadFong(ctx):
    # The intent for this function is to web scrape data from 247Sports and eventually display Crystal Ball updates from Wiltfong.
    # Currently receiving a 500 Internal Server Error each pull
    url = 'https://247sports.com/User/Steve%20Wiltfong/Predictions/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    page_response = requests.get(url, timeout=5,headers=headers)
    page_content = BeautifulSoup(page_response.content, "html.parser")

    #li class="name"
    #span regex => xxx / #-# / ###
    #b regex => #.####
    #li class="prediction"
    #span class="prediction-date"
    #li class="correct"

    print(page_content.find_all(id="main-photo"),'\n')

# Retrieve the Discord Bot Token
f = open("../token.txt","r")
bot.run(f.readline())