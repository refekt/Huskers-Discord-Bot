#!/usr/bin/env python3.6
import discord
from discord.ext import commands
from discord.utils import get
import requests
import sys
import random
import json
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
async def crootbot(ctx):
    #pulls a json file from the 247 advanced player search API and parses it to give
    #info on the croot.
    #First, pull the message content, split the individual pieces, and make the api call
    croot_info = ctx.message.content.strip().split() 
    year = int(croot_info[1])
    first_name = croot_info[2]
    last_name = croot_info[3]
    url = 'https://247sports.com/Season/{}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={}&Player.LastName={}'.format(year, first_name, last_name)
    headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
    search = requests.get(url=url, headers=headers)
    search = json.loads(search.text)
    if not search:
        await ctx.send("I could not find any player named {} {} in the {} class".format(first_name, last_name, year))
    else:
        search = search[0] #The json that is returned is a list of dictionaries, I pull the first item in the list (may consider adding complexity)
        player = search['Player']
        first_name = player['FirstName']
        last_name = player['LastName']
        position = player['PrimaryPlayerPosition']['Abbreviation']
        hometown = player['Hometown']
        state = hometown['State']
        city = hometown['City']
        height = player['Height'].replace('-', "'") + '"'
        weight = player['Weight']
        high_school = player['PlayerHighSchool']['Name']
        image_url = player['DefaultAssetUrl']
        embed = discord.Embed(title = 'CrootPic')
        embed.set_image(url=image_url)
        composite_rating = player['CompositeRating']/100
        composite_star_rating = player['CompositeStarRating']
        national_rank = player['NationalRank']
        position_rank = player['PositionRank']
        state_rank = player['StateRank']
        player_url = player['Url']
        stars = ''
        for i in range(int(composite_star_rating)):
            stars += '\N{WHITE MEDIUM STAR}'
        
        title = '**{} {}** - {}'.format(first_name, last_name, stars)
        body = '**{}, Class of {}**\n{}, {}lbs -- From {}, {}({})\n247 Composite Rating: {:.4f}\n247 Link - {}'.format(position, year, height, int(weight), city, state, high_school, composite_rating, player_url)
        await ctx.send(title)
        await ctx.send(embed=embed)
        await ctx.send(body)
    

@client.command()
async def billyfacts(ctx):
    facts = []
    with open("facts.txt") as f:
        for line in f:
            facts.append(line)
    f.close()

    random.shuffle(facts)
    await ctx.message.channel.send(random.choice(facts))


@client.command()
async def randomflag(ctx):
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

@client.command()    
async def huskerbotquit(ctx):
    await client.logout()


# Retrieve the Discord Bot Token
f = open("config.txt", "r")
client.run(f.readline())
f.close()
