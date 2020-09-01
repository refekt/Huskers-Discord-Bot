import asyncio
import hashlib
import json
import logging
import random
import re
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

import utils.consts as consts
from cogs.images import build_quote
from utils.consts import CHAN_HOF_PROD, CHAN_HOF_TEST, CHAN_BOTLOGS, CHAN_WAR_ROOM, CHAN_SCOTT, CHAN_SCOTTS_BOTS, CHAN_BANNED, CHAN_TEST_SPAM, CHAN_STATS_BANNED, CHAN_TWITTERVERSE, CHAN_GENERAL, \
    CHAN_IOWA
from utils.consts import EMBED_TITLE_HYPE
from utils.consts import FOOTER_SECRET
from utils.consts import GUILD_TEST, GUILD_PROD
from utils.consts import ROLE_POTATO, ROLE_ASPARAGUS, ROLE_AIRPOD, ROLE_ISMS, ROLE_MEME, ROLE_PACKER, ROLE_PIXEL, ROLE_RUNZA, ROLE_MINECRAFT, ROLE_HYPE_MAX, ROLE_HYPE_SOME, ROLE_HYPE_NO, ROLE_TIME_OUT
from utils.consts import change_my_nickname, change_my_status
from utils.embed import build_embed
from utils.misc import on_prod_server
from utils.mysql import process_MySQL, sqlLogUser, sqlRecordStats, sqlRetrieveTasks, sqlRetrieveIowa
from utils.thread import send_reminder, send_math

tweet_reactions = ("🎈", "🌽", "🕸")


async def current_guild():
    guild = None
    if sys.argv[1] == "prod":
        guild = client.get_guild(GUILD_PROD)
    elif sys.argv[1] == "test":
        guild = client.get_guild(GUILD_TEST)
    return guild


async def split_payload(payload):
    p = dict()
    p["channel_id"] = client.get_channel(payload.channel_id)
    p["emoji"] = payload.emoji
    guild = client.get_guild(payload.guild_id)
    p["guild_id"] = guild.id
    # p["user_id"] = client.get_user(payload.user_id)
    p["user_id"] = guild.get_member(payload.user_id)
    c = client.get_channel(payload.channel_id)
    # c = await client.fetch_channel(payload.channel_id)
    p["message"] = await c.fetch_message(payload.message_id)

    del c
    del payload

    return p


async def process_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        if type(ctx.channel) == discord.channel.DMChannel:
            chan = "DM"
        else:
            chan = ctx.channel.name

        embed = build_embed(
            title="BotFrost Error Message",
            description=str(error),
            fields=[
                ["Author", ctx.message.author],
                ["Message ID", ctx.message.id],
                ["Channel", chan],
                ["Content", ctx.message.clean_content]
            ]
        )
        await ctx.send(embed=embed)


async def compare_users(before: discord.Member, after: discord.Member):
    differences = []

    if not before.display_name == after.display_name:
        differences.append(f"{before.display_name} >> {after.display_name}")

    if not before.nick == after.nick:
        differences.append(f"{before.nick} >> {after.nick}")

    if not before.status == after.status:
        differences.append(f"{before.status} >> {after.status}")

    if not before.roles == after.roles:
        differences.append(f"{before.roles} >> {after.roles}")

    return str([diff for diff in differences])


async def monitor_messages(message: discord.Message):
    channel = client.get_channel(message.channel.id)

    async def auto_replies():
        myass = ("https://66.media.tumblr.com/b9a4c96d0c83bace5e3ff303abc08f1f/tumblr_oywc87sfsP1w8f7y5o3_500.gif",
                 "https://66.media.tumblr.com/2ae73f93fcc20311b00044abc5bad05f/tumblr_oywc87sfsP1w8f7y5o1_500.gif",
                 "https://66.media.tumblr.com/102d761d769840a541443da82e0b211a/tumblr_oywc87sfsP1w8f7y5o5_500.gif",
                 "https://66.media.tumblr.com/252fd1a689f0f64cb466b4eced502af7/tumblr_oywc87sfsP1w8f7y5o2_500.gif",
                 "https://66.media.tumblr.com/83eb614389b1621be0ce9890b1998644/tumblr_oywc87sfsP1w8f7y5o4_500.gif",
                 "https://66.media.tumblr.com/f833da26820867601cd7ad3a7c2d96a5/tumblr_oywc87sfsP1w8f7y5o6_500.gif", "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo1_250.gif",
                 "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo2_250.gif", "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo3_250.gif",
                 "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo4_250.gif", "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo6_250.gif")

        if re.search(r"fuck (you|u) bot", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="BITE MY SHINY, METAL ASS",
                    image=random.choice(myass)
                ),
                content=message.author.mention
            )

        elif re.search(r"love (you|u) bot", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="Shut Up Baby, I Know It",
                    image="https://media1.tenor.com/images/c1fd95af4433edf940fdc8d08b411622/tenor.gif?itemid=7506108"
                ),
                content=message.author.mention
            )

        elif re.search(r"good bot", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="😝",
                    image="https://i.imgur.com/52v1upi.png"
                ),
                content=message.author.mention
            )

        elif re.search(r"bad bot", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="╰（‵□′）╯",
                    image="https://i.redd.it/6vznew4w92211.jpg"
                ),
                content=message.author.mention
            )

        # elif re.search(r"(should|could|would|might)\sof", message.content, re.IGNORECASE):
        #     await channel.send(
        #         embed=build_embed(
        #             title="Grammar Police",
        #             fields=[
        #                 ["Fix yourself!", "~~of~~ have*"],
        #                 ["Not My Idea", "This was <@440885775132000266>'s idea!"]
        #             ]
        #         )
        #     )

        elif "isms" in message.content.lower():
            if random.random() >= .99:
                await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and make **shit** up for fake internet points. I'm glad he's gone.")

        # if not type(channel) == discord.DMChannel and ROLE_GUMBY in [roleid.id for roleid in message.author.roles]:
        #     #     # blocked = False
        #     #     try:
        #     #         if not message.author.is_blocked():
        #     #             await message.add_reaction("🦐")
        #     #         else:
        #     #             print(f"Unable to add 🦐 reaction to {message.author}'s message because I am blocked by them!")
        #     #     except discord.Forbidden:
        #     #         print(f"Unable to add 🦐 reaction to {message.author}'s message. They most likely blocked me!")
        #     #
        #     if random.random() >= .99:
        #         await message.channel.send(f"{message.author.mention} https://i.imgur.com/1tVJ2tW.gif")

    async def find_subreddits():
        subreddits = re.findall(r"r\/[a-zA-Z0-9]{1,}", message.content.lower())

        if len(subreddits) > 0:
            subs = []

            for index, s in enumerate(subreddits):
                if [sub for sub in ["huskers", "cfb"] if (sub in s)]:
                    return

                url = 'https://reddit.com/' + s
                if '.com//r/' in url:
                    url = url.replace('.com//r', '.com/r')
                subs.append([s, url])

            await message.channel.send(
                embed=build_embed(
                    title="Found Subreddits",
                    fields=subs,
                    inline=False
                )
            )

    async def add_votes():
        arrows = ("⬆", "⬇", "↔")

        if ".addvotes" in message.content.lower():
            for arrow in arrows:
                await message.add_reaction(arrow)

    async def record_statistics():
        if not type(message.channel) == discord.DMChannel:
            author = str(message.author).encode("ascii", "ignore").decode("ascii")
            channel = f"{message.guild}.#{message.channel.name}".encode("ascii", "ignore").decode("ascii")

            process_MySQL(query=sqlRecordStats, values=(author, channel))

    if not message.author.bot:
        if message.channel.id not in CHAN_BANNED:
            await auto_replies()

        if message.channel.id not in CHAN_STATS_BANNED:
            await record_statistics()

        if not [ele for ele in client.all_commands.keys() if (ele in message.content)]:
            await find_subreddits()

        await add_votes()


async def twitterverse(message: discord.Message):
    if message.channel.id == CHAN_TWITTERVERSE:
        for reaction in tweet_reactions:
            await message.add_reaction(reaction)


async def monitor_reactions(channel, emoji: discord.PartialEmoji, user: discord.Member, message: discord.Message):
    async def trivia_message():
        from cogs.games.trivia import reactions, game, tally_score

        if not user.bot and game.started and emoji.name in reactions:
            try:
                if message.embeds[0].title == "Husker Discord Trivia" and emoji.name in reactions:
                    question_search = f"{emoji}: {game.questions[game.current_question]['correct']}"
                    result = re.search(question_search, message.embeds[0].fields[1].value)

                    if result:
                        tally_score(message, user, datetime.now())
                    else:
                        tally_score(message, user, 0)
            except:
                print("Error when processing scores")

            try:
                for reaction in message.reactions:
                    await reaction.remove(user)
            except TypeError:
                pass

    async def twitterverse_reacts():
        for react in message.reactions:
            if react.count > 2:
                return

        async def send_tweet(channel):
            def embeds_exist():
                if len(message.embeds) == 0:
                    return False
                else:
                    return True

            share_string = f"[Shared by {user}]: "

            if embeds_exist():
                await channel.send(content=share_string + message.content, embed=message.embeds[0])
            else:
                await channel.send(content=share_string + message.content)

        if emoji.name == tweet_reactions[0] and not tweet_reactions[0] in message.content:  # Balloon = General
            c = client.get_channel(CHAN_GENERAL)
            await send_tweet(c)

        elif emoji.name == tweet_reactions[1] and not tweet_reactions[1] in message.content:  # Corn = Scotts
            c = client.get_channel(CHAN_SCOTT)
            await send_tweet(c)

        elif emoji.name == tweet_reactions[2] and user.id == 189554873778307073:
            pass

    async def quote_reacts():
        # if not channel.id in [CHAN_SCOTTS_BOTS, CHAN_NORTH_BOTTTOMS, CHAN_POSSUMS]:
        #     return
        # raise AttributeError(f"You are not allowed to use this command in this channel!")

        quote_emoji = "📝"
        reactions = message.reactions
        already_run = False
        for reaction in reactions:
            if reaction.emoji == quote_emoji and reaction.count > 1:
                already_run = True

        if not already_run and emoji.name == quote_emoji and message.reactions:
            await channel.send(
                file=build_quote(
                    quote=message.clean_content,
                    author=message.author
                )
            )

    await trivia_message()
    await quote_reacts()

    if not user.bot:
        await twitterverse_reacts()


async def hall_of_fame_messages(reactions: list):
    HOF_chan = client.get_channel(id=CHAN_HOF_PROD)

    if HOF_chan is None:
        HOF_chan = client.get_channel(id=CHAN_HOF_TEST)

    message_history_raw = []
    duplicate = False

    def server_member_count():
        return len(client.users)

    threshold = int(0.0047 * server_member_count())

    for reaction in reactions:
        if reaction.count >= threshold and not reaction.message.channel.name == HOF_chan.name and not ".addvotes" in reaction.message.content:
            if not reaction.message.author.bot:
                message_history_raw = await HOF_chan.history(limit=5000).flatten()

                for message_raw in message_history_raw:
                    if len(message_raw.embeds) > 0:
                        if message_raw.embeds[0].footer.text == str(reaction.message.id):
                            duplicate = True
                            break

                if not duplicate:
                    embed = discord.Embed(title=f"🏆 » Husker Discord Hall of Fame Message by [ {reaction.message.author} ] with the [ {reaction} ] reaction « 🏆",
                                          color=0xFF0000)
                    embed.add_field(name=f"Author: {reaction.message.author}", value=f"{reaction.message.content}", inline=False)
                    embed.add_field(name="View Message", value=f"[View Message]({reaction.message.jump_url})", inline=False)
                    embed.set_footer(text=reaction.message.id)
                    await HOF_chan.send(embed=embed)

    del message_history_raw
    del duplicate


async def monitor_msg_roles(action, message: discord.Message, member: discord.User, emoji: discord.Emoji):
    roles_title = "Huskers' Discord Roles"
    try:
        if message.embeds[0].title == roles_title:
            # guild = client.get_guild(GUILD_PROD)
            guild = await current_guild()
            member = guild.get_member(member.id)
            roles = {
                "🥔": guild.get_role(ROLE_POTATO),
                "💚": guild.get_role(ROLE_ASPARAGUS),
                "🥪": guild.get_role(ROLE_RUNZA),
                "😹": guild.get_role(ROLE_MEME),
                "♣": guild.get_role(ROLE_ISMS),
                "🧀": guild.get_role(ROLE_PACKER),
                "☎": guild.get_role(ROLE_PIXEL),
                "🎧": guild.get_role(ROLE_AIRPOD),
                "🪓": guild.get_role(ROLE_MINECRAFT)
            }

            if not emoji.name in [emoji for emoji in roles.keys()]:
                return

            bot_logs = client.get_channel(id=CHAN_BOTLOGS)

            if action == "add":
                await member.add_roles(roles[emoji.name], reason=roles_title)
                # await bot_logs.send(f"Added [{roles[emoji.name].mention}] to user [{member.mention}].")
            elif action == "remove":
                await member.remove_roles(roles[emoji.name], reason=roles_title)
                # await bot_logs.send(f"Removed [{roles[emoji.name].mention}] to user [{member.mention}].")
    except IndexError:
        pass


async def monitor_msg_hype(action, message: discord.Message, member: discord.Member, emoji: discord.Emoji):
    # guild = client.get_guild(GUILD_PROD)
    # if guild is None:
    #     guild = client.get_guild(GUILD_TEST)
    guild = await current_guild()

    role_hype_max = guild.get_role(ROLE_HYPE_MAX)
    role_hype_some = guild.get_role(ROLE_HYPE_SOME)
    role_hype_no = guild.get_role(ROLE_HYPE_NO)
    hypesquad = [role_hype_max, role_hype_some, role_hype_no]

    try:
        if message.embeds[0].title == EMBED_TITLE_HYPE:

            member = guild.get_member(member.id)
            roles = {
                "📈": role_hype_max,
                "⚠": role_hype_some,
                "⛔": role_hype_no,
            }

            if emoji.name not in [emoji for emoji in roles.keys()]:
                return

            bot_logs = client.get_channel(id=CHAN_BOTLOGS)

            if action == "add":
                await member.add_roles(roles[emoji.name], reason=EMBED_TITLE_HYPE)
                # await bot_logs.send(f"Added [{roles[emoji.name].mention}] to user [{member.mention}].")
            elif action == "remove":
                await member.remove_roles(roles[emoji.name], reason=EMBED_TITLE_HYPE)
                # await bot_logs.send(f"Removed [{roles[emoji.name].mention}] to user [{member.mention}].")
    except IndexError:
        pass


async def load_tasks():
    tasks = process_MySQL(sqlRetrieveTasks, fetch="all")
    guild = await current_guild()

    def convert_duration(value: str):
        imported_datetime = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
        now = datetime.now()

        if imported_datetime > now:
            duration = imported_datetime - now
            return duration
        return None

    async def convert_member(value):
        value = int(value)
        try:
            member = guild.get_member(value)
            if member is not None:
                return member
        except:
            pass

        try:
            channel = guild.get_channel(value)
            if channel is not None:
                return channel
        except:
            pass

        return None

    if tasks is None:
        print("No tasks loaded")
        return

    print(f"### ;;; There are {len(tasks)} to be loaded")

    task_repo = []

    for task in tasks:
        send_when = convert_duration(task["send_when"])
        member_or_chan = await convert_member(task["send_to"])

        if member_or_chan is None:
            print(f"### ;;; Skipping task because [{member_or_chan}] is None.")
            continue

        if task["author"] is None:
            task["author"] = "N/A"

        if send_when is None:
            print(f"### ;;; Alert time already passed! {task['send_when']}")
            await send_reminder(
                thread=None,
                duration=-1,
                who=member_or_chan,
                message=task["message"],
                author=task["author"],
                flag=task["send_when"])
            continue

        task_repo.append(
            asyncio.create_task(
                send_reminder(
                    thread=member_or_chan.id + send_when.total_seconds(),
                    duration=send_when.total_seconds(),
                    who=member_or_chan,
                    message=task["message"],
                    author=task["author"],
                    flag=task["send_when"]
                )
            )
        )

    for index, task in enumerate(task_repo):
        await task


async def start_maths():
    print("### /// Start maths")
    guild = await current_guild()
    math_channel = guild.get_channel(CHAN_SCOTTS_BOTS)
    discord_math = asyncio.create_task(send_math(math_channel))
    await discord_math
    print("### /// Finished maths")


class MyClient(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

    async def send_salutations(self, msg: str):
        guild = await current_guild()
        channel = None
        if sys.argv[1] == "prod":
            channel = guild.get_channel(CHAN_SCOTTS_BOTS)
        elif sys.argv[1] == "test":
            channel = guild.get_channel(CHAN_TEST_SPAM)

        await channel.send(msg)

    async def startup_procedures(self):
        appinfo = await self.application_info()

        await change_my_status(client)
        await change_my_nickname(client, ctx=None)
        # await start_maths()
        await load_tasks()

        print(
            f"### The bot is ready! ###\n"
            f"### Bot Frost version 2.0 (Loaded at {datetime.now()}) ###\n"
            f"### ~~~ Name: {client.user}\n"
            f"### ~~~ ID: {client.user.id}\n"
            f"### ~~~ Description: {appinfo.description}\n"
            f"### ~~~ Onwer Name: {appinfo.owner.name}#{appinfo.owner.discriminator}\n"
            f"### ~~~ Owner ID: {appinfo.owner.id}\n"
            f"### ~~~ Owner Created: {appinfo.owner.created_at}\n"
            f"### ~~~ Latency: {self.latency * 1000:.2f} MS\n"
            f"### ~~~ Command Prefix: \"{self.command_prefix}\""
        )

        # channels = guild.channels
        # for channel in channels:
        #     print(f"### Channel - {channel.name} & {channel.id}")

    def send_to_log(self, type, msg):
        if type == logging.DEBUG:
            logging.debug(msg)
        elif type == logging.INFO:
            logging.info(msg)
        elif type == logging.WARNING:
            logging.warning(msg)
        elif type == logging.ERROR:
            logging.error(msg)
        elif type == logging.CRITICAL:
            logging.critical(msg)

    if on_prod_server():
        async def on_command_error(self, ctx, error):
            if ctx.message.content.startswith(f"{client.command_prefix}secret"):
                try:
                    error_message = f"Incorrect message format. Use: {client.command_prefix}secret <mammal> <channel> <message>"
                    context = ctx.message.content.split(" ")

                    if context[0].lower() != f"{client.command_prefix}secret":
                        await ctx.message.author.send(error_message)
                        return

                    if not context[1].isalpha() and not context[2].isalpha():
                        await ctx.message.author.send(error_message)
                        return

                    if context[2].lower() != "war" and context[2].lower() != "scott":
                        await ctx.message.author.send(error_message)
                        return

                    f = open('mammals.json', 'r')
                    temp_json = f.read()
                    mammals = json.loads(temp_json)
                    f.close()

                    checkID = hashlib.md5(str(ctx.message.author.id).encode())

                    if context[2].lower() == "war":
                        channel = client.get_channel(CHAN_WAR_ROOM)
                    elif context[2].lower() == "scott":
                        channel = client.get_channel(CHAN_SCOTT)
                    else:
                        await ctx.message.author.send(error_message)
                        return

                    if checkID.hexdigest() == mammals[context[1]]:
                        context_commands = f"{context[0]} {context[1]} {context[2]}"
                        message = ctx.message.content[len(context_commands):]

                        embed = discord.Embed(title="Secret Mammal Messaging System (SMMS)", color=0xD00000)
                        embed.set_thumbnail(url="https://i.imgur.com/EGC1qNt.jpg")
                        embed.set_footer(text=FOOTER_SECRET)
                        embed.add_field(name="Back Channel Communications", value=message)

                        await channel.send(embed=embed)
                    else:
                        await ctx.message.authro.send("Shit didn't add up")
                        return
                except:
                    await process_error(ctx, error)
            elif error.args[0] == "Command raised an exception: RuntimeError: This event loop is already running":
                return
            elif error == TypeError:
                return
            else:
                # get data from exception
                etype = type(error)
                trace = error.__traceback__

                # the verbosity is how large of a traceback to make
                # more specifically, it's the amount of levels up the traceback goes from the exception source
                verbosity = 4

                # 'traceback' is the stdlib module, `import traceback`.
                lines = traceback.format_exception(etype, error, trace, verbosity)

                # format_exception returns a list with line breaks embedded in the lines, so let's just stitch the elements together
                traceback_text = ''.join(lines)

                # now we can send it to the user
                # it would probably be best to wrap this in a codeblock via e.g. a Paginator
                print(traceback_text)

                await process_error(ctx, error)

    # async def on_shard_ready(self, shard_id):
    #     pass
    #     # logging.info(f"[on_shard_ready] Shard ID: {shard_id}")

    # async def on_socket_raw_receive(self, msg):
    #     pass
    #     # self.send_to_log(logging.INFO, msg)

    # async def on_socket_raw_send(self, payload):
    #     pass
    #     # self.send_to_log(logging.INFO, payload)

    async def on_connect(self):
        async for guild in client.fetch_guilds():
            if guild.id not in (GUILD_TEST, GUILD_PROD):
                try:
                    print(f"### ### !!! Stranger danger. Leaving guild [{guild}]!")
                    await guild.leave()
                except discord.HTTPException:
                    print(f"### ### !!! Leaving guild failed!")
                    pass

        # process_MySQL(query=sqlDatabaseTimestamp, values=(str(client.user), True, str(datetime.now())))
        await self.startup_procedures()
        # await self.send_salutations(f"*Beep, boop* Greetings! I have arrived.")

    # async def on_disconnect(self):
    #     pass
    #     # process_MySQL(query=sqlDatabaseTimestamp, values=(str(client.user), False, str(datetime.now())))
    #
    #     # await self.send_salutations("I AM DISCONNECTING.")

    # async def on_ready(self):
    #     # await self.send_salutations("Ready to go Cap-i-tan!")
    #     pass

    async def on_resume(self):
        await change_my_status(client)
        await change_my_nickname(client, ctx=None)

        await self.send_salutations("I have returned!")

    async def on_message(self, message):

        if message.webhook_id:
            await twitterverse(message)

        await monitor_messages(message)

        if message.channel.id not in CHAN_BANNED:
            await self.process_commands(message)  # Always needed to process commands
        # else:
        #     raise PermissionError(f"I am not authorized to perform commands in {message.channel.name}.\nMessage: {message.clean_content}")

    # async def on_message_delete(self, message):
    #     pass

    # async def on_bulk_message_delete(self, message):
    #     pass

    # async def on_raw_message_delete(self, payload):
    #     pass

    # async def on_raw_bulk_message_delete(self, payload):
    #     pass

    # async def on_message_edit(self, before, after):
    #     pass

    # async def on_raw_message_edit(self, payload):
    #     pass

    # async def on_reaction_add(reaction, user):
    #     pass

    async def on_raw_reaction_add(self, payload):
        payload = await split_payload(payload)

        if not payload["message"].channel.id in CHAN_BANNED:
            await hall_of_fame_messages(payload["message"].reactions)

        await monitor_reactions(channel=payload["channel_id"], emoji=payload["emoji"], user=payload["user_id"], message=payload["message"])
        await monitor_msg_roles(action="add", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])
        await monitor_msg_hype(action="add", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])

    # async def on_reaction_remove(reaction, user):
    #     pass

    async def on_raw_reaction_remove(self, payload):
        payload = await split_payload(payload)

        await monitor_msg_roles(action="remove", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])
        await monitor_msg_hype(action="remove", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])

    # async def on_reaction_clear(self, message, reactions):
    #     pass

    # async def on_raw_reaction_clear(self, payload):
    #     pass

    async def on_member_join(self, member):
        process_MySQL(query=sqlLogUser, values=(f"{member.name}#{member.discriminator}", "member_join", "N/A"))

        iowegians = process_MySQL(
            query=sqlRetrieveIowa,
            fetch="all"
        )

        if not iowegians:
            return

        timeout = member.guild.get_role(ROLE_TIME_OUT)
        iowa = member.guild.get_channel(CHAN_IOWA)

        for iowegian in iowegians:
            if member.id == iowegian["user_id"]:
                await iowa.send(f"[ {member.mention} ] left the server and has been returned to {iowa.mention}.")
                await member.add_roles(timeout, reason="Back to Iowa")
                return

    async def on_member_remove(self, member):
        process_MySQL(query=sqlLogUser, values=(f"{member.name}#{member.discriminator}", "remove", "N/A"))

    # async def on_member_update(self, before, after):
    #     pass

    async def on_user_udpate(self, before, after):
        process_MySQL(query=sqlLogUser, values=(f"{before.name}#{before.discriminator}", "user_update", await compare_users(before, after)))

    async def on_member_ban(self, guild, user):
        process_MySQL(query=sqlLogUser, values=(f"{user.name}#{user.discriminator}", "ban", "N/A"))

    async def on_member_unban(self, guild, user):
        process_MySQL(query=sqlLogUser, values=(f"{user.name}#{user.discriminator}", "unban", "N/A"))


if on_prod_server():
    command_prefix = "$"
else:
    command_prefix = "%"

client = MyClient(command_prefix=command_prefix, case_insensitive=True, description="Husker Discord Bot: Bot Frost", owner_id=189554873778307073)
extensions = (
    "cogs.admin", "cogs.flags", "cogs.images", "cogs.referee", "cogs.schedule", "cogs.text", "cogs.croot", "cogs.games.trivia", "cogs.games.minecraft", "cogs.games.tcg.tcg",
    "cogs.betting", 'cogs.music', 'cogs.reddit', 'cogs.message_history', 'cogs.deepfry', 'cogs.fap')

for extension in extensions:
    try:
        client.load_extension(extension)
        print(f"### Successfully loaded [{extension}] commands! ###")
    except:
        traceback.print_exc()

if len(sys.argv) > 0:
    if on_prod_server():
        token = consts.PROD_TOKEN
    else:
        token = consts.TEST_TOKEN

    print("### Starting the bot...")
    client.run(token)
    print("### The bot has been started!")
else:
    print("No arguments provided!")
