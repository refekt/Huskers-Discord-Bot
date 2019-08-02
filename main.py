#!/usr/bin/env python3.7
import discord
from discord.ext import commands
from discord.utils import get
import requests
from bs4 import BeautifulSoup
import sys
import random
import config
import re
import cogs.croot_bot

# Bot specific stuff
botPrefix='$'
client = commands.Bot(command_prefix=botPrefix)

# Cogs
client.load_extension('cogs.image_commands')
client.load_extension('cogs.text_commands')
client.load_extension('cogs.croot_bot')

# initialize a global list for CrootBot to put search results in
# player_search_list = []
authorized_to_quit = [440639061191950336, 443805741111836693, 189554873778307073, 339903241204793344, 606301197426753536]

welcome_emoji_list = ['🔴', '🍞', '🥔', '🥒', '😂']
emoji_list = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
huskerbot_footer="Generated by HuskerBot"
welcome_footer='HusekrBot welcomes you!'
wrong_channel_text='The command you sent is not authorized for use in this channel.'

profile_url = None
highlight_url = None


# Start bot (client) events
@client.event
async def on_ready():
    # https://gist.github.com/scragly/2579b4d335f87e83fbacb7dfd3d32828
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Husker football 24/7"))
    print("***\nLogged in as [{0}].\nDiscord.py version is: [{1}].\nDiscord version is [{2}].\n***".format(client.user, discord.__version__, sys.version))


@client.event
async def on_message(message):
    """ Commands processed as messages are entered """
    if not message.author.bot:
        #get a list of subreddits mentioned
        subreddits = re.findall(r'(?:^| )(/?r/[a-z]+)', message.content)
        if len(subreddits) > 0:
            embed = discord.Embed(title="Found Subreddits")
            for s in subreddits:
                url='https://reddit.com/' + s
                if '.com//r/' in url:
                    url = url.replace('.com//r', '.com/r')
                embed.add_field(name = s, value = url, inline = False)
            await message.channel.send(embed = embed)

        # Good bot, bad bot       
        if "good bot" in message.content.lower():
            await message.channel.send("OwO thanks")
        elif "bad bot" in message.content.lower():
            embed = discord.Embed(title="I'm a bad, bad bot")
            embed.set_image(url='https://i.imgur.com/qDuOctd.gif')
            await message.channel.send(embed=embed)

        # Husker Bot hates Isms
        if "isms" in message.content.lower():
            dice_roll = random.randint(1,101)
            if dice_roll >= 90:
                await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and "
                                           "make **shit** up for fake internet points. I'm glad he's gone.")

        # Add Up Votes and Down Votes
        if (".addvotes") in message.content.lower():
            # Upvote = u"\u2B06" or "\N{UPWARDS BLACK ARROW}"
            # Downvote = u"\u2B07" or "\N{DOWNWARDS BLACK ARROW}"
            emojiUpvote="\N{UPWARDS BLACK ARROW}"
            emojiDownvote="\N{DOWNWARDS BLACK ARROW}"
            await message.add_reaction(emojiUpvote)
            await message.add_reaction(emojiDownvote)

    # HUDL highlight puller on react. This section is to take the crootbot message, find if a hudl profile exists, and pull the video. 
    # Next would be to monitor reactions and post the video if someone reacted to the video camera emoji.
    # TODO If there are multiple football players with the same name we may get the wrong guy. Especially for croots from previous classes. We will want to add more logic to narrow 
    # TODO it down even more
    if len(message.embeds) > 0:
        # Welcome message detection
        if message.author == client.user and message.embeds[0].footer.text == welcome_footer:
            i = 0
            while i < len(welcome_emoji_list):
                await message.add_reaction(welcome_emoji_list[i])
                i += 1

        # CrootBot Search Results detection
        if message.author == client.user and config.player_search_list and message.embeds[0].footer.text == 'Search Results ' + huskerbot_footer:
            # Pre-add reactions for users
            i = 0
            while i < min(10, len(config.player_search_list)):
                await message.add_reaction(emoji_list[i])
                i += 1

        # CrootBot dection
        if message.author == client.user and message.embeds[0].footer.text == huskerbot_footer:
            # print("***\nChecking for highlight video")
            # global profile_url
            url = config.profile_url + 'videos' #bugging here?
            headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
            page = requests.get(url = url, headers = headers)
            soup = BeautifulSoup(page.text, 'html.parser')
            videos = soup.find_all(class_='title_lnk')
            if len(videos) > 0:
                # "Highlight video found")
                global highlight_url
                highlight_url = videos[0].get('href')
                for v in videos:
                    if 'senior' in v.get('title').lower():                       
                        highlight_url = v.get('href')
                        break
                    elif 'junior' in v.get('title').lower():
                        highlight_url = v.get('href')
                        break
                    elif 'sophomore' in v.get('title').lower():
                        highlight_url = v.get('href')
                # print("{}\n***".format(highlight_url))
                embed_old = message.embeds[0]
                embed_new = embed_old.set_footer(text='Click the video camera emoji to get a highlight video for this recruit')
                await message.edit(embed=embed_new)
                await message.add_reaction('📹')
            else:
                # "No highlight video found\n***")
            config.profile_url = None

    # Always need this
    await client.process_commands(message)


@client.event
async def on_member_join(member):
    embed = discord.Embed(title="HuskerBot's Welcome Message", color=0xff0000)
    embed.add_field(name="Welcome __`{}`__ to the Huskers Discord!".format(member.name), value="The Admin team and Frost Approved members hope you have a good time while here. I am your full-serviced Discord bot, HuskerBot! You can find a list of my commands by sending `$help`.\n\n"
                   "We also have some fun roles that may interest you and you're welcome to join! The first, we have the 🔴 `@Lil' Huskers Squad`--those who are fans of Lil Red. Next up we have the 🍞 `@/r/unza` team. They are our resident Runza experts. Right behind the sandwich lovers are the 😂 `@Meme Team`! Their meme creation is second to none. Finally, we have our two food gangs: 🥔 `@POTATO GANG` and 🥒 `@Asparagang`. Which is better?\n\n"
                   "React to this message with the emojis below to automatically join the roles!", inline=False)
    embed.set_footer(text=welcome_footer)

    # welcome_channel = client.get_channel(487431877792104470)
    # await welcome_channel.send(embed=embed)
    await member.send(embed=embed)


@client.event
async def on_reaction_add(reaction, user):
    # Checking for an embedded message
    if len(reaction.message.embeds) > 0:
        # Debugging
        # print("***\nEmbeds > 0")

        if user != client.user and reaction.message.author == client.user and config.player_search_list and reaction.message.embeds[0].footer.text == 'Search Results ' + huskerbot_footer:
            channel = reaction.message.channel

            emoji_dict = {'1⃣': 0,
                          '2⃣': 1,
                          '3⃣': 2,
                          '4⃣': 3,
                          '5⃣': 4,
                          '6⃣': 5,
                          '7⃣': 6,
                          '8⃣': 7,
                          '9⃣': 8,
                          '🔟': 9
                          }

            if reaction.emoji in emoji_dict:
                cb = cogs.croot_bot.CrootBot
                await cb.parse_search(self=reaction, search=config.player_search_list[emoji_dict[reaction.emoji]], channel=channel)

        # If a 247 highlight is found for a crootbot response and someone reacts to the video camera, call the function to parse through the recruits hudl page and grab a highlight video
        global highlight_url

        if user != client.user and reaction.message.author == client.user and reaction.message.embeds[0].footer.text == 'Click the video camera emoji to get a highlight video for this recruit' and highlight_url is not None:
            # Debugging
            # print("Highlight videos")

            if reaction.emoji == '📹':                
                channel = reaction.message.channel
                headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
                url = highlight_url
                page = requests.get(url = url, headers = headers)
                soup = BeautifulSoup(page.text, 'html.parser')

                try:
                    video_url = soup.find(class_='video-wrapper').find('iframe').get('src')
                except:
                    video_url = soup.find(class_='video-container').find('iframe').get('src')
                if 'https:' not in video_url:
                    video_url='https:' + video_url   
                title = soup.find(class_='video-block').find_all('div')[2].find('h3').get_text()
                embed = discord.Embed(title = title, url = video_url, color=0xff0000)
                await channel.send(embed = embed)
                highlight_url = None

        # Adding roles to member
        # if user != client.user and reaction.message.author == client.user and reaction.message.embeds[0].footer.text == huskerbot_footer:
        if reaction.emoji in welcome_emoji_list and user != client.user:
            # Debugging
            print("New member joins")

            server_id = 440632686185414677
            server = client.get_guild(server_id)
            member = server.get_member(user.id)

            if reaction.emoji == '🍞':
                role = get(server.roles, id=485086088017215500)
                await member.add_roles(role)
            elif reaction.emoji == '😂':
                role = get(server.roles, id=448690298760200195)
                await member.add_roles(role)
            elif reaction.emoji == '🥒':
                role = get(server.roles, id=583842403341828115)
                await member.add_roles(role)
            elif reaction.emoji == '🥔':
                role = get(server.roles, id=583842320575889423)
                await member.add_roles(role)
            elif reaction.emoji == '🔴':
                role = get(server.roles, id=464903715854483487)
                await member.add_roles(role)
    else:
        # Debugging
        # print("***\nEmbeds <= 0\n***")

    # print("***")


@client.event
async def on_command_error(ctx, error):
    output_msg="Whoa there {}! Something went wrong. {}. Please review `$help` for a list of all available commands.".format(ctx.message.author, error)
    await ctx.send(output_msg)
# End bot (client) events


# Admin command
@client.command(aliases=["quit", "q"])
async def huskerbotquit(ctx):
    """ Did HuskerBot act up? Use this only in emergencies. """
    authorized = False

    for r in ctx.author.roles:
        # # await ctx.send("Name: `{}`\n, ID: `{}`".format(r.name, r.id))
        if r.id in authorized_to_quit:
             authorized = True

    if authorized:
        await ctx.send("You are authorized to turn me off. Good bye cruel world 😭.")
        print("!!! I was turned off by '{}' in '{}'.".format(ctx.author, ctx.channel))
        await client.logout()
    else:
        await ctx.send("Nice try buddy! 👋")
# Admin command


# Run the Discord bot
# Does nothing if no sys.argv present
if len(sys.argv) > 0:
    if sys.argv[1] == 'test':
        print("*** Running development server")
        client.run(config.TEST_TOKEN)
    elif sys.argv[1] == 'prod':
        print("*** Running production server")
        client.run(config.DISCORD_TOKEN)
    else:
        print("You are error. Good bye!")
