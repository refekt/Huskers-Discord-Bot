#!/usr/bin/env python3.7

# Bot name ideas: Bot Frost, Mario Verbotzco, Adrian Botinez, Bot Devaney, Mike Rilbot, Robo Pelini, Devine Ozigbot, Mo Botty, Bot Moos,

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
from cogs.text_commands import load_season_bets
from cogs.text_commands import store_next_opponent
import datetime
import json

# Bot specific stuff
botPrefix='$'
client = commands.Bot(command_prefix=botPrefix)

# Cogs
client.load_extension('cogs.image_commands')
client.load_extension('cogs.text_commands')
client.load_extension('cogs.croot_bot')
client.load_extension('cogs.stat_bot')
client.load_extension('cogs.sched_commands')

# initialize a global list for CrootBot to put search results in
authorized_to_quit = [440639061191950336, 443805741111836693, 189554873778307073, 339903241204793344, 606301197426753536]
banned_channels = [440868279150444544, 607399402881024009]

welcome_emoji_list = ['🔴', '🍞', '🥔', '🥒', '😂']
emoji_list = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]
huskerbot_footer="Generated by HuskerBot"
welcome_footer='HusekrBot welcomes you!'
wrong_channel_text='The command you sent is not authorized for use in this channel.'

profile_url = None
highlight_url = None
season_year = int(datetime.date.today().year) - 2019  # Future proof
bet_counter = -1


def try_adding_new_dict(bet_username: str, which: str, placed_bet: str):
    # Check if the user betting has already placed a bet
    raw_username = bet_username
    raw_datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    game = config.current_game[0].lower()  # Grabs the opponent from current_game[]
    game_bets = config.season_bets[season_year]['opponent'][game]['bets']

    for bet_users in game_bets:
        for users in bet_users:
            if str(users) == raw_username:
                if which == "winorlose":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": placed_bet, "spread": bet_users[users]['spread'], "moneyline": bet_users[users]['moneyline']}
                elif which == "canx_winorlose":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": placed_bet, "spread": bet_users[users]['spread'], "moneyline": bet_users[users]['moneyline']}
                elif which == "spread":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": bet_users[users]['winorlose'], "spread": placed_bet, "moneyline": bet_users[users]['moneyline']}
                elif which == "canx_spread":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": bet_users[users]['winorlose'], "spread": placed_bet, "moneyline": bet_users[users]['moneyline']}
                elif which == "moneyline":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": bet_users[users]['winorlose'], "spread": bet_users[users]['spread'], "moneyline": placed_bet}
                elif which == "canx_moneyline":
                    config.new_dict = {"datetime": raw_datetime, "winorlose": bet_users[users]['winorlose'], "spread": bet_users[users]['spread'], "moneyline": placed_bet}
            else:
                pass               # print("No match")

    global bet_counter  # I don't think this actually does anything. Probably can be replaced with 0 or 1
    try:
        for bet_users in config.season_bets[season_year]['opponent'][game]['bets']:
            bet_users[raw_username] = config.new_dict
            bet_counter += 1

    # Setup a new nested mess of variables to translate into JSON
    except:
        # Write to JSON file
        config.season_bets[season_year]['opponent'][game]['bets'][raw_username].append(config.new_dict)
        with open("season_bets.json", "w") as json_file:
            json.dump(config.season_bets, json_file, sort_keys=True, indent=4)


# Start bot (client) events
@client.event
async def on_ready():
    # https://gist.github.com/scragly/2579b4d335f87e83fbacb7dfd3d32828
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Husker football 24/7"))
    print("*** Version Information:\n    Logged in as [{0}].\n    Discord.py version is: [{1}].\n    Discord version is [{2}].\n***".format(client.user, discord.__version__, sys.version))


@client.event
async def on_message(message):
    """ Commands processed as messages are entered """
    if not message.author.bot:
        # Add Up Votes and Down Votes
        if (".addvotes") in message.content.lower():
            # Upvote = u"\u2B06" or "\N{UPWARDS BLACK ARROW}"
            # Downvote = u"\u2B07" or "\N{DOWNWARDS BLACK ARROW}"
            emojiUpvote = "\N{UPWARDS BLACK ARROW}"
            emojiDownvote = "\N{DOWNWARDS BLACK ARROW}"
            await message.add_reaction(emojiUpvote)
            await message.add_reaction(emojiDownvote)

        # Reply to NotA_Virus
        if not message.channel in banned_channels:
            #get a list of subreddits mentioned
            subreddits = re.findall(r'(?:^| )(/?r/[a-z]+)', message.content.lower())
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
            elif "fuck you bot" in message.content.lower():
                await message.channel.send("Whoa {}, that's not very nice!".format(message.author.mention))

            # Husker Bot hates Isms
            if "isms" in message.content.lower():
                dice_roll = random.randint(1,101)
                if dice_roll >= 90:
                    await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and "
                                               "make **shit** up for fake internet points. I'm glad he's gone.")

            notavirus = "NotaVirus_Click#3411"
            if str(message.author).lower() == notavirus.lower():
                dice_roll = random.randint(1, 101)
                if dice_roll > 65:
                    if "you suck" in message.content.lower():
                        await message.channel.send("HEY NOW! I am on to you {}...".format(message.author.mention))
                    elif "eggplant" in message.content.lower():
                        await message.channel.send("Attention: {} loves eggplant.".format(message.author.mention))
                    elif "🍆" in message.content:
                        await message.channel.send("🍆💦")
                else:
                    # print("Missed dice roll for {}".format(notavirus))
                    pass

    # Check for HuskerBot embedded messages.
    if len(message.embeds) > 0:
        # Welcome message detection. Adds reactions to message to allow user to self-assign "fun roles."
        if message.author == client.user and message.embeds[0].footer.text == welcome_footer:
            i = 0
            while i < len(welcome_emoji_list):
                await message.add_reaction(welcome_emoji_list[i])
                i += 1

        # CrootBot Search Results detection. Adds reactions to message to allow user to click to pull a search result.
        # TODO If there are multiple football players with the same name we may get the wrong guy. Especially for croots from previous classes. We will want to add more logic to narrow it down even more
        if message.author == client.user and config.player_search_list and message.embeds[0].footer.text == 'Search Results ' + huskerbot_footer:
            # Pre-add reactions for users
            i = 0
            while i < min(10, len(config.player_search_list)):
                await message.add_reaction(emoji_list[i])
                i += 1

        # $CrootBot message dection. Looks for a HUDL profile and attempts to pull a highlight video from the player's profile. Adds a reaction 🎥 to click on to show video.
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
                if videos:
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
                    print("No videos found?")
            else:
                # "No highlight video found\n***")
                pass
            config.profile_url = None

    # Always need this
    await client.process_commands(message)


@client.event
async def on_member_join(member):
    print("New member: {}".format(member.name))
    embed = discord.Embed(title="HuskerBot's Welcome Message", color=0xff0000)
    embed.add_field(name="Welcome __`{}`__ to the Huskers Discord!".format(member.name), value="The Admin team and Frost Approved members hope you have a good time while here. I am your full-serviced Discord bot, HuskerBot! You can find a list of my commands by sending `$help`.\n\n"
                   "We also have some fun roles that may interest you and you're welcome to join! The first, we have the 🔴 `@Lil' Huskers Squad`--those who are fans of Lil Red. Next up we have the 🍞 `@/r/unza` team. They are our resident Runza experts. Right behind the sandwich lovers are the 😂 `@Meme Team`! Their meme creation is second to none. Finally, we have our two food gangs: 🥔 `@POTATO GANG` and 🥒 `@Asparagang`. Which is better?\n\n"
                   "React to this message with the emojis below to automatically join the roles!", inline=False)
    embed.set_footer(text=welcome_footer)
    await member.send(embed=embed)

    # channel_join = client.get_channel(458474143403212801)
    # embed_join = discord.Embed(title="Member Joined", color=0xFF0000)
    # embed_join.add_field(name="Member Name", value=member.name)
    # embed_join.add_field(name="ID", value=member.id)
    # await channel_join.send(embed=embed_join)
    pass

# Client events for member leave, ban, unban, etc.
# @client.event
# async def on_member_remove(member):
#     channel_join = client.get_channel(458474143403212801)
#     embed_join = discord.Embed(title="Member Left", color=0xFF0000)
#     embed_join.add_field(name="Member Name", value=member.name)
#     embed_join.add_field(name="ID", value=member.id)
#     await channel_join.send(embed=embed_join)
#
#
# @client.event
# async def on_member_ban(guild, user):
#     channel_join = client.get_channel(458474143403212801)
#     embed_join = discord.Embed(title="Member Banned", color=0xFF0000)
#     embed_join.add_field(name="Member Name", value=user.name)
#     embed_join.add_field(name="ID", value=user.id)
#     await channel_join.send(embed=embed_join)
#
#
# @client.event
# async def on_member_unban(guild, user):
#     channel_join = client.get_channel(458474143403212801)
#     embed_join = discord.Embed(title="Member Unbanned", color=0xFF0000)
#     embed_join.add_field(name="Member Name", value=user.name)
#     embed_join.add_field(name="ID", value=user.id)
#     await channel_join.send(embed=embed_join)
#
#
# @client.event
# async def on_user_update(before, after):
#     channel_join = client.get_channel(458474143403212801)
#     embed_join = discord.Embed(title="Member Updated", color=0xFF0000)
#     embed_join.add_field(name="Member Name Before", value="{}#{}".format(before.name, before.discriminator))
#     embed_join.add_field(name="Member Name After", value="{}#{}".format(after.name, after.discriminator))
#     await channel_join.send(embed=embed_join)


@client.event
async def on_reaction_add(reaction, user):
    # Checking for an embedded message
    if len(reaction.message.embeds) > 0:
        # Checking for $CrootBot search results embedded message. Responds to added reactions by searching for and outputting a 247Sports profile for that player.
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

        # If a 247 highlight is found for a $CrootBot response and someone reacts to the video camera, call the function to parse through the recruits hudl page and grab a highlight video
        global highlight_url
        if user != client.user and reaction.message.author == client.user and reaction.message.embeds[0].footer.text == 'Click the video camera emoji to get a highlight video for this recruit' and highlight_url is not None:
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

        # Checking for on_member_join() embedded message. Adds "fun role" to member based on which reaction is sent.
        if reaction.emoji in welcome_emoji_list and user != client.user and reaction.message.embeds[0].footer.text == welcome_footer:
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

        # Updating season_bets JSON for reacting to a $bet message
        # TODO Add datetime checking for kickoff through midnight of the same day.
        if reaction.emoji in bet_emojis and user != client.user and reaction.message.embeds[0].footer.text == config.bet_footer:
            # Load season_bets.json if season_bets{} is empty
            if not bool(config.season_bets):
                load_season_bets()
            # Load current game if empty
            if not bool(config.current_game):
                store_next_opponent()

            check_now = datetime.datetime.now()
            check_game_datetime_raw = config.current_game[1]
            check_game_datetime = datetime.datetime(day=check_game_datetime_raw.day, month=check_game_datetime_raw.month, year=check_game_datetime_raw.year, hour=check_game_datetime_raw.hour, minute=check_game_datetime_raw.minute, second=check_game_datetime_raw.second, microsecond=check_game_datetime_raw.microsecond)

            if check_now > check_game_datetime:
                await user.send("Unable to place bet because the game has started. You can review your placed bets by using `$bet show`.")
                return

            raw_username = "{}#{}".format(user.name, user.discriminator)
            game = config.current_game[0].lower()  # Grabs the opponent from current_game[]

            if reaction.emoji == "⬆":
                try_adding_new_dict(raw_username, "winorlose", "True")
            elif reaction.emoji == "⬇":
                try_adding_new_dict(raw_username, "winorlose", "False")
            elif reaction.emoji == "❎":
                try_adding_new_dict(raw_username, "canx_winorlose", "None")
            elif reaction.emoji == "⏫":
                try_adding_new_dict(raw_username, "spread", "True")
            elif reaction.emoji == "⏬":
                try_adding_new_dict(raw_username, "spread", "False")
            elif reaction.emoji == "❌":
                try_adding_new_dict(raw_username, "canx_spread", "None")
            elif reaction.emoji == "🔼":
                try_adding_new_dict(raw_username, "moneyline", "True")
            elif reaction.emoji == "🔽":
                try_adding_new_dict(raw_username, "moneyline", "False")
            elif reaction.emoji == "✖":
                try_adding_new_dict(raw_username, "canx_moneyline", "None")
            else:
                pass

            # Send a message alerting the channel that a user has placed a bet.
            global bet_counter

            # *** Maybe change to a PM instead ***
            # Creates the embed object for all messages within method
            embed = discord.Embed(title="Husker Game Betting", color=0xff0000)
            embed.set_thumbnail(url="https://i.imgur.com/THeNvJm.jpg")
            embed.set_footer(text=config.bet_footer)

            for u in config.season_bets[season_year]['opponent'][game]['bets'][bet_counter]:
                if u == raw_username:
                    embed.add_field(name="Author", value=raw_username, inline=False)
                    embed.add_field(name="Opponent", value=config.current_game[0], inline=False)
                    embed.add_field(name="Win or Loss", value=config.new_dict['winorlose'], inline=True)
                    embed.add_field(name="Spread", value=config.new_dict['spread'], inline=True)
                    await user.send(embed=embed)
            bet_counter = -1

            # Remove reaction to prevent user from voting for both
            try:
                #print("Bot's add_reaction permission: {}".format(user))
                await reaction.remove(user)
            except discord.Forbidden as forb:
                print("Unable to remove {}'s reaction due to Forbiddin: \n{}".format(user, forb))
            except discord.HTTPException as err:
                print("Error removing reaction from {}: {}".format(user, err))
            except:
                print("I don't know why we can't remove {}'s reaction.".format(user))

            with open("season_bets.json", "w") as json_file:
                json.dump(config.season_bets, json_file, sort_keys=True, indent=4)
    else:
        pass


@client.event
async def on_command_completion(ctx):
    global banned_channels

    if ctx.channel.id in banned_channels:
        not_authed = "⚠ This channel is banned from using commands ⚠"

        async for message in ctx.channel.history(limit=2, oldest_first=False):
            if message.author == client.user:
                await message.delete()

        await ctx.send(not_authed)


# TODO Check if command is Animal: Hashed-username
# @client.event
async def on_command_error(ctx, error):
    output_msg ="Whoa there, {}! Something went doesn't look quite right. Please review `$help` for further assistance. Contact my creators if the problem continues.\n" \
                "```Message ID: {}\n" \
                "Channel: {} / {}\n" \
                "Author: {}\n" \
                "Content: {}\n" \
                "Error: {}```".format(ctx.message.author.mention, ctx.message.id, ctx.message.channel.name, ctx.message.channel.id, ctx.message.author, ctx.message.content, error)
    await ctx.send(output_msg)
# End bot (client) events

# Admin command
@client.command(hidden=True)
async def squirrel(ctx, chan, *, message):
    if str(ctx.author) == "IDontBelieveInIsms#1838":
        if chan.lower() == "war":
            channel = client.get_channel(525519594417291284)
            embed = discord.Embed(title="Secret Squirrel Message", color=0xFF0000)
            embed.add_field(name="Content", value=message)
            await channel.send(embed=embed)
        elif chan.lower() == "scott":
            channel = client.get_channel(507520543096832001)
            embed = discord.Embed(title="Secret Squirrel Message", color=0xFF0000)
            embed.add_field(name="Content", value=message)
            await channel.send(embed=embed)
        else:
            await ctx.send("Incorrect channel provided. \"war\" and \"scott\" are the only options.")
            return

@client.command(hidden=True)
async def chipmunk(ctx, chan, *, message):
    authorized = False

    for r in ctx.author.roles:
        if r.id == 443805741111836693 or r.id == 440639061191950336:
            authorized = True

    if authorized:
        if chan.lower() == "war":
            channel = client.get_channel(525519594417291284)
            embed = discord.Embed(title="Secret Chipmunk Message", color=0xFF0000)
            embed.add_field(name="Content", value=message)
            await channel.send(embed=embed)
        elif chan.lower() == "scott":
            channel = client.get_channel(507520543096832001)
            embed = discord.Embed(title="Secret Chipmunk Message", color=0xFF0000)
            embed.add_field(name="Content", value=message)
            await channel.send(embed=embed)
        else:
            await ctx.send("Incorrect channel provided. \"war\" and \"scott\" are the only options.")
            return

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


@client.command()
async def about(ctx):
    embed = discord.Embed(title="HuskerBot's CV", author=client.user, color=0xFF0000)
    embed.set_thumbnail(url="https://i.imgur.com/Ah3x5NA.png")
    embed.add_field(name="About HuskerBot", value="HuskerBot was created by [/u/refekt](https://reddit.com/u/refekt) and "
                                                  "[/u/psyspoop](https://reddit.com/u/psyspoop). Jeyrad and ModestBeaver assist greatly with coding. "
                                                  "Source code is located on "
                                                  "[GitHub](https://www.github.com/refekt/Husker-Bot).")
    embed.add_field(name="Hosting Location", value="Jeyrad's VPS Server. Thank you!")
    embed.add_field(name="Current Latency", value="{:.2f} ms".format(client.latency*1000))
    embed.add_field(name="Client User", value=client.user)
    embed.add_field(name="Ready Status", value=client.is_ready())
    await ctx.send(embed=embed)

if len(sys.argv) == 0:
    print("*** Running production server ***")
    client.run(config.DISCORD_TOKEN)
else:
    if sys.argv[1] == 'test':
        print("*** Running development server ***")
        client.run(config.TEST_TOKEN)
    print("You are error. Good bye!")
