#!/usr/bin/env python3.6
import discord
from discord.ext import commands
from discord.utils import get
import requests
import sys
import random
from bs4 import BeautifulSoup


botPrefix = '$'
client = commands.Bot(command_prefix=botPrefix)


@client.event
async def on_ready():
    print("Logged in as {0}. Discord.py version is: [{1}] and Discord version is [{2}]".format(client.user, discord.__version__, sys.version))
    # print("The client has the following emojis:\n", client.emojis)


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
                                       "make **shit** up for fake internet points. I’m glad he’s gone.")
        # Add Up Votes and Down Votes
        # Work In Progress
        # https://discordpy.readthedocs.io/en/latest/faq.html#how-can-i-add-a-reaction-to-a-message

        if (".addvotes") in message.content.lower():
            # Upvote = u"\u2B06" or "\N{UPWARDS BLACK ARROW}"
            # Downvote = u"\u2B07" or "\N{DOWNWARDS BLACK ARROW}"
            emojiUpvote = "\N{UPWARDS BLACK ARROW}"
            emojiDownvote = "\N{DOWNWARDS BLACK ARROW}"
            print("Upvote: {0} and Downvote: {1}".format(emojiUpvote, emojiDownvote))
            try:
                await message.add_reaction(emojiUpvote)
                await message.add_reaction(emojiDownvote)
            except:
                pass

    await client.process_commands(message)


@client.command()
async def billyfacts(ctx):
    """ Real facts about Bill Callahan """
    facts = []
    with open("facts.txt") as f:
        for line in f:
            facts.append(line)
    f.close()

    random.shuffle(facts)
    await ctx.message.channel.send(random.choice(facts))


@client.command()
async def randomflag(ctx):
    """ A random ass, badly made Nebraska flag """
    flags = []
    with open("flags.txt") as f:
        for line in f:
            flags.append(line)
    f.close()

    random.shuffle(flags)
    embed = discord.Embed(title="Random Ass Nebraska Flag")
    embed.set_image(url=random.choice(flags))
    await ctx.send(embed=embed)


@client.command()
async def iowasux(ctx):
    """ Iowa has the worst corn """
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
async def flex(ctx):
    """ S T R O N K """
    embed = discord.Embed(title="FLEXXX 😩")
    embed.set_image(url='https://i.imgur.com/92b9uFU.gif')
    await ctx.send(embed=embed)

@client.command()
async def shrug(ctx):
    """ Who knows 😉 """
    embed = discord.Embed(title="🤷‍♀️")
    embed.set_image(url='https://i.imgur.com/Yt63gGE.gif')
    await ctx.send(embed=embed)


@client.command()
async def ohno(ctx):
    """ This is not ideal """
    embed = discord.Embed(title="Big oof")
    embed.set_image(url='https://i.imgur.com/f4P6jBO.png')
    await ctx.send(embed=embed)


@client.command()
async def bigsexy(ctx):
    """ Give it to me Kool Aid man """
    embed = discord.Embed(title="OOOHHH YEAAHHH 😩")
    embed.set_image(url='https://i.imgur.com/UpKIx5I.png')
    await ctx.send(embed=embed)


# Retrieve the Discord Bot Token
f = open("config.txt", "r")
client.run(f.readline())
f.close()
