#!/usr/bin/env python3.6
import discord
from discord.ext import commands
from discord.utils import get
import requests
import sys
from bs4 import BeautifulSoup

client = commands.Bot(command_prefix='$')


@client.event
async def on_ready():
    print("Logged in as {0}. Discord.py version is: [{1}] and Discord version is [{2}]".format(client.user, discord.__version__, sys.version))
    # print("The client has the following emojis:\n", client.emojis)


'''@client.event
async def on_reaction_add(reaction, user):
    await reaction.message.channel.send('{} has added {} to the messge: {}'.format(user.name, reaction.emoji, 
    reaction.message.content))'''


''''@client.event
async def on_typing(channel, user, when):
    print("{0} is typing in {1}!".format(user, channel))'''


@client.event
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
            await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and "
                                       "make shut up for fake internet points. I’m glad he’s gone.")

    await client.process_commands(message)


@client.command()
async def clear(ctx):
    msgs = []
    async for msg in client.logs_from(ctx.message.channel):
        if msg.author.id == ctx.author.bot:
            msgs.append(msg)
        await client.delete_messages(msgs)


@client.command()
async def iowasux(ctx):
    await ctx.message.channel.send("You're god damn right they do, {0}!".format(ctx.message.author))
    emoji = client.get_emoji(441038975323471874)
    await ctx.message.add_reaction(emoji)
    await ctx.message.channel.send(emoji)


@client.command()
async def stonk(ctx):
    """ Isms hates stocks """
    await ctx.send("Stonk!")


@client.command()
async def potatoes(ctx):
    """ Potatoes are love; potatoes are life """
    embed = discord.Embed(title="Po-Tay-Toes")
    embed.set_image(url='https://i.imgur.com/Fzw6Gbh.gif')
    await ctx.send(embed=embed)


@client.command()
async def loadFong(ctx):
    # The intent for this function is to web scrape data from 247Sports and eventually display Crystal Ball updates
    # from Wiltfong.
    # Currently receiving a 500 Internal Server Error each pull
    url = 'https://247sports.com/User/Steve%20Wiltfong/Predictions/'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/39.0.2171.95 Safari/537.36'}
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
client.run(f.readline())