import asyncio
import hashlib
import json
import random
import re
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands

import utils.consts as consts
from cogs.images import build_quote
from utils.consts import CHAN_HOF_PROD, CHAN_HOF_TEST, CHAN_WAR_ROOM, CHAN_SCOTT, CHAN_BANNED, CHAN_STATS_BANNED, \
    CHAN_GENERAL, CHAN_IOWA, CHAN_RULES
from utils.consts import FOOTER_SECRET
from utils.consts import GUILD_TEST, GUILD_PROD
from utils.consts import ROLE_POTATO, ROLE_ASPARAGUS, ROLE_AIRPOD, ROLE_ISMS, ROLE_MEME, ROLE_PACKER, ROLE_PIXEL, ROLE_RUNZA, \
    ROLE_MINECRAFT, ROLE_HYPE_MAX, ROLE_HYPE_SOME, ROLE_HYPE_NO, ROLE_TIME_OUT
from utils.consts import TWITTER_BOT_MEMBER
from utils.embed import build_embed
from utils.misc import on_prod_server
from utils.mysql import process_MySQL, sqlRecordStats, sqlRetrieveTasks, sqlRetrieveIowa
from utils.thread import send_reminder


class BotFrostClient(commands.Bot):
    tweet_reactions = ("🎈", "🌽")

    def current_guild(self):
        if sys.argv[1] == "prod":
            return client.get_guild(GUILD_PROD)
        elif sys.argv[1] == "test":
            return client.get_guild(GUILD_TEST)

    def is_iowegian(self, member: discord.Member):
        return process_MySQL(
            query=sqlRetrieveIowa,
            values=member.id,
            fetch="all"
        )

    async def monitor_messages(self, message: discord.Message):
        async def auto_replies():
            myass = ("https://66.media.tumblr.com/b9a4c96d0c83bace5e3ff303abc08f1f/tumblr_oywc87sfsP1w8f7y5o3_500.gif",
                     "https://66.media.tumblr.com/2ae73f93fcc20311b00044abc5bad05f/tumblr_oywc87sfsP1w8f7y5o1_500.gif",
                     "https://66.media.tumblr.com/102d761d769840a541443da82e0b211a/tumblr_oywc87sfsP1w8f7y5o5_500.gif",
                     "https://66.media.tumblr.com/252fd1a689f0f64cb466b4eced502af7/tumblr_oywc87sfsP1w8f7y5o2_500.gif",
                     "https://66.media.tumblr.com/83eb614389b1621be0ce9890b1998644/tumblr_oywc87sfsP1w8f7y5o4_500.gif",
                     "https://66.media.tumblr.com/f833da26820867601cd7ad3a7c2d96a5/tumblr_oywc87sfsP1w8f7y5o6_500.gif",
                     "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo1_250.gif",
                     "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo2_250.gif",
                     "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo3_250.gif",
                     "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo4_250.gif",
                     "https://66.media.tumblr.com/tumblr_m7e2ahFFDo1qcuoflo6_250.gif")
            embed = None

            if re.search(r"fuck (you|u) bot", message.content, re.IGNORECASE):
                embed = build_embed(
                    title="BITE MY SHINY, METAL ASS",
                    image=random.choice(myass)
                )

            elif re.search(r"love (you|u) bot", message.content, re.IGNORECASE):
                embed = build_embed(
                    title="Shut Up Baby, I Know It",
                    image="https://media1.tenor.com/images/c1fd95af4433edf940fdc8d08b411622/tenor.gif?itemid=7506108"
                )

            elif "good bot" in message.content.lower():
                embed = build_embed(
                    title="😝",
                    image="https://i.imgur.com/52v1upi.png"
                )

            elif "bad bot" in message.content.lower():
                embed = build_embed(
                    title="╰（‵□′）╯",
                    image="https://i.redd.it/6vznew4w92211.jpg"
                )

            if embed is not None:
                return await message.channel.send(content=message.author.mention, embed=embed)

        async def add_votes():
            if ".addvotes" in message.content.lower():
                for arrow in ("⬆", "⬇", "↔"):
                    await message.add_reaction(arrow)

        async def record_statistics():
            if not type(message.channel) == discord.DMChannel:
                author = str(message.author).encode("ascii", "ignore").decode("ascii")
                chan = f"{message.guild}.#{message.channel.name}".encode("ascii", "ignore").decode("ascii")
                process_MySQL(query=sqlRecordStats, values=(author, chan))

        if message.channel.id not in CHAN_BANNED:
            await auto_replies()

        if message.channel.id not in CHAN_STATS_BANNED:
            await record_statistics()

        await add_votes()

    async def check_current_guild(self):
        async for guild in client.fetch_guilds():
            if guild.id not in (GUILD_TEST, GUILD_PROD):
                try:
                    print(f"### ### !!! Stranger danger. Leaving guild [{guild}]!")
                    await guild.leave()
                except discord.HTTPException:
                    print(f"### ### !!! Leaving guild failed!")
                await client.logout()

    async def change_my_status(self):
        statuses = (
            "Husker Football 24/7",
            "Currently beating Florida 62-24",
            "Currently giving up 400 yards rushing to one guy",
            "Attempting a swing pass for -1 yards",
            "Missing a PAT or a missing a 21 yard FG",
            "Getting wasted in Haymarket"
        )
        try:
            print("~~~ Attempting to change status...")
            new_activity = random.choice(statuses)
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=new_activity))
            print(f"~~~ Changed status to '{new_activity}'")
        except AttributeError as err:
            err_msg = "~~~ !!! " + str(err).replace("\n", " ")
            print(err_msg)
        except discord.HTTPException as err:
            err_msg = "~~~ !!! " + str(err).replace("\n", " ")
            print(err_msg)
        except:
            print(f"~~~ !!! Unknown error!", sys.exc_info()[0])

    async def change_my_nickname(self):
        nicks = (
            "Bot Frost", "Mario Verbotzco", "Adrian Botinez", "Bot Devaney", "Mike Rilbot", "Robo Pelini", "Devine Ozigbot",
            "Mo Botty", "Bot Moos", "Luke McBotfry", "Bot Diaco", "Rahmir Botson",
            "I.M. Bott", "Linux Phillips", "Dicaprio Bottle", "Bryce Botheart", "Jobot Chamberlain", "Bot Bando",
            "Shawn Botson",
            "Zavier Botts", "Jimari Botler", "Bot Gunnerson", "Nash Botmacher",
            "Botger Craig", "Dave RAMington", "MarLAN Lucky", "Rex Bothead", "Nbotukong Suh", "Grant Bostrom",
            "Ameer Botdullah",
            "Botinic Raiola", "Vince Ferraboto", "economybot",
            "NotaBot_Human", "psybot", "2020: the year of the bot", "bottech129", "deerebot129")

        try:
            print("~~~ Attempting to change nickname...")
            await client.user.edit(username=random.choice(nicks))
            print(f"~~~ Changed nickname to {client.user.display_name}")
        except discord.HTTPException as err:
            err_msg = "~~~ !!! " + str(err).replace("\n", " ")
            print(err_msg)
        except:
            print(f"~~~ !!! Unknown error!", sys.exc_info()[0])

    async def load_tasks(self):
        tasks = process_MySQL(sqlRetrieveTasks, fetch="all")
        guild = self.current_guild()

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
            return print("No tasks loaded")

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

    async def process_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        else:
            if type(ctx.channel) == discord.channel.DMChannel:
                channel = "DM"
            else:
                channel = ctx.channel.name

            embed = build_embed(
                title="BotFrost Error Message",
                description=str(error),
                fields=[
                    ["Author", ctx.message.author],
                    ["Channel", channel],
                    ["Content", ctx.message.clean_content]
                ]
            )
            await ctx.send(embed=embed)

    async def monitor_reactions(self, channel, emoji: discord.PartialEmoji, user: discord.Member, message: discord.Message):
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

        async def twitter_reacts():
            for react in message.reactions:
                if react.count > 2:
                    return

            async def send_tweet(ch):
                share_string = f"[Shared by {user.mention}]: "
                await ch.send(content=share_string + message.content, embed=message.embeds[0])

            if emoji.name == self.tweet_reactions[0] and not self.tweet_reactions[0] in message.content:  # Balloon = General
                c = client.get_channel(CHAN_GENERAL)
                await send_tweet(c)

            elif emoji.name == self.tweet_reactions[1] and not self.tweet_reactions[1] in message.content:  # Corn = Scotts
                c = client.get_channel(CHAN_SCOTT)
                await send_tweet(c)

            # elif emoji.name == self.tweet_reactions[2]:  # Web = Reddit
            #     await user.send(f"Here is your post URL!\n"
            #                     f"https://www.reddit.com/r/huskers/submit?title=&text={message.embeds[0].fields[1].value}")

        async def quote_reacts():
            quote_emoji = "📝"
            already_run = False

            for reaction in message.reactions:
                if reaction.emoji == quote_emoji and reaction.count > 1:
                    already_run = True

            if not already_run and emoji.name == quote_emoji and message.reactions:
                await channel.send(
                    file=build_quote(
                        quote=message.clean_content,
                        author=message.author
                    )
                )

        if not user.bot:
            await trivia_message()
            await quote_reacts()
            await twitter_reacts()

    async def role_reactions(self, action, message: discord.Message, member: discord.User, emoji: discord.Emoji):
        roles_title = ("Huskers' Discord Roles", "Nebraska Football Hype Squad 📈 ⚠ ⛔")
        try:
            if message.embeds[0].title in roles_title:
                guild = self.current_guild()
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
                    "🪓": guild.get_role(ROLE_MINECRAFT),
                    "📈": guild.get_role(ROLE_HYPE_MAX),
                    "⚠": guild.get_role(ROLE_HYPE_SOME),
                    "⛔": guild.get_role(ROLE_HYPE_NO),
                }

                if emoji.name not in [emoji for emoji in roles.keys()]:
                    return

                print(
                    type(roles[emoji.name])
                )

                if action == "add":
                    await member.add_roles(roles[emoji.name], reason="User added a role from #rules")
                elif action == "remove":
                    await member.remove_roles(roles[emoji.name], reason="User removed a role from #rules")
        except IndexError:
            pass

    async def hall_of_fame_messages(self, reactions: list):
        hof_channel = client.get_channel(id=CHAN_HOF_PROD)

        if hof_channel is None:
            hof_channel = client.get_channel(id=CHAN_HOF_TEST)

        duplicate = False
        server_member_count = len(client.users)
        threshold = int(0.0047 * server_member_count)
        message_history_raw = None

        for reaction in reactions:
            if reaction.count >= threshold and reaction.message.channel.id != hof_channel.id and ".addvotes" not in reaction.message.content:
                message_history_raw = await hof_channel.history(limit=5000).flatten()

                # Check for duplicate HOF messages. Message ID is stored in the footer for comparison.
                for message_raw in message_history_raw:
                    if len(message_raw.embeds) > 0:
                        if str(reaction.message.id) in message_raw.embeds[0].footer.text:
                            duplicate = True
                            break

                if not duplicate:
                    embed = build_embed(
                        title=f"🏆🏆🏆 Hall of Fame Message 🏆🏆🏆",
                        fields=[
                            [f"{reaction.message.author} said...", f"{reaction.message.content}"],
                            ["HOF Reaction", reaction],
                            ["Message Link", f"[Click to view message]({reaction.message.jump_url})"]
                        ],
                        inline=False,
                        footer=f"Hall of Fame message created at {reaction.message.created_at.strftime('%B %d, %Y at %H:%M%p')} | Message ID: {reaction.message.id}"
                    )
                    return await hof_channel.send(embed=embed)

        del message_history_raw, duplicate, server_member_count

    async def split_payload(self, payload):
        guild = client.get_guild(payload.guild_id)
        c = client.get_channel(payload.channel_id)

        payload_dict = dict()
        payload_dict["channel_id"] = client.get_channel(payload.channel_id)
        payload_dict["emoji"] = payload.emoji
        payload_dict["guild_id"] = guild.id
        payload_dict["user_id"] = guild.get_member(payload.user_id)
        payload_dict["message"] = await c.fetch_message(payload.message_id)

        del c, payload

        return payload_dict

    async def twitterverse(self, message: discord.Message):
        for reaction in self.tweet_reactions:
            await message.add_reaction(reaction)

    if on_prod_server():
        async def on_command_error(self, ctx, error):
            if ctx.message.content.startswith(f"{client.command_prefix}secret"):
                try:
                    error_message = f"Incorrect message format. Use: {client.command_prefix}secret <mammal> <channel> <message>"
                    context = ctx.message.content.split(" ")

                    if context[0].lower() != f"{client.command_prefix}secret":
                        return await ctx.message.author.send(error_message)

                    if not context[1].isalpha() and not context[2].isalpha():
                        return await ctx.message.author.send(error_message)

                    if context[2].lower() != "war" and context[2].lower() != "scott":
                        return await ctx.message.author.send(error_message)

                    f = open('mammals.json', 'r')
                    temp_json = f.read()
                    mammals = json.loads(temp_json)
                    f.close()

                    check_id = hashlib.md5(str(ctx.message.author.id).encode())

                    if context[2].lower() == "war":
                        channel = client.get_channel(CHAN_WAR_ROOM)
                    elif context[2].lower() == "scott":
                        channel = client.get_channel(CHAN_SCOTT)
                    else:
                        return await ctx.message.author.send(error_message)

                    if check_id.hexdigest() == mammals[context[1]]:
                        context_commands = f"{context[0]} {context[1]} {context[2]}"
                        message = ctx.message.content[len(context_commands):]

                        embed = discord.Embed(title="Secret Mammal Messaging System (SMMS)", color=0xD00000)
                        embed.set_thumbnail(url="https://i.imgur.com/EGC1qNt.jpg")
                        embed.set_footer(text=FOOTER_SECRET)
                        embed.add_field(name="Back Channel Communications", value=message)

                        await channel.send(embed=embed)
                    else:
                        return await ctx.message.authro.send("Shit didn't add up")
                except:
                    await self.process_error(ctx, error)
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
                # it would probably be best to wrap this in a code block via e.g. a Paginator
                print(traceback_text)

                await self.process_error(ctx, error.original)

    async def on_connect(self):
        appinfo = await self.application_info()

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

        await self.change_my_status()
        await self.change_my_nickname()
        await self.check_current_guild()
        await self.load_tasks()

    async def on_message(self, message):

        if not message.author.bot:
            if message.author.id == TWITTER_BOT_MEMBER:
                await self.twitterverse(message)

            await self.monitor_messages(message)

            if message.channel.id not in CHAN_BANNED:
                return await self.process_commands(message)  # Always needed to process commands

    async def on_raw_reaction_add(self, payload):
        payload = await self.split_payload(payload)

        if payload["message"].channel.id == CHAN_RULES:
            await self.role_reactions(action="add", message=payload["message"], member=payload["user_id"],
                                      emoji=payload["emoji"])

        if payload["message"].channel.id not in CHAN_BANNED and not payload["user_id"].bot:
            await self.hall_of_fame_messages(payload["message"].reactions)

        await self.monitor_reactions(channel=payload["channel_id"], emoji=payload["emoji"], user=payload["user_id"],
                                     message=payload["message"])

    async def on_raw_reaction_remove(self, payload):
        payload = await self.split_payload(payload)

        if payload["message"].channel.id == CHAN_RULES:
            await self.role_reactions(action="remove", message=payload["message"], member=payload["user_id"],
                                      emoji=payload["emoji"])

    async def on_member_join(self, member):
        if not self.is_iowegian(member):
            return

        timeout = member.guild.get_role(ROLE_TIME_OUT)
        iowa = member.guild.get_channel(CHAN_IOWA)

        await iowa.send(f"[ {member.mention} ] left the server and has been returned to {iowa.mention}.")
        await member.add_roles(timeout, reason="Back to Iowa")

    # Unused Events
    # async def on_resume(self):
    # async def on_shard_ready(self, shard_id):
    # async def on_socket_raw_receive(self, msg):
    # async def on_socket_raw_send(self, payload):
    # async def on_disconnect(self):
    # async def on_ready(self):
    # async def on_message_delete(self, message):
    # async def on_bulk_message_delete(self, message):
    # async def on_raw_message_delete(self, payload):
    # async def on_raw_bulk_message_delete(self, payload):
    # async def on_message_edit(self, before, after):
    # async def on_raw_message_edit(self, payload):
    # async def on_reaction_add(reaction, user):
    # async def on_reaction_remove(reaction, user):
    # async def on_reaction_clear(self, message, reactions):lea
    # async def on_raw_reaction_clear(self, payload):
    # async def on_member_remove(self, member):
    # async def on_member_update(self, before, after):
    # async def on_user_udpate(self, before, after):
    # async def on_member_ban(self, guild, user):
    # async def on_member_unban(self, guild, user):


if on_prod_server():
    command_prefix = "$"
else:
    command_prefix = "%"

client_intents = discord.Intents().all()

client = BotFrostClient(
    command_prefix=command_prefix,
    case_insensitive=True,
    description="Husker Discord Bot: Bot Frost",
    owner_id=189554873778307073,
    intents=client_intents
)

extensions = (
    # "cogs.admin",
    # "cogs.flags",
    # "cogs.images",
    # "cogs.referee",
    # "cogs.schedule",
    # "cogs.text",
    # "cogs.croot",
    # "cogs.games.trivia",
    # "cogs.games.minecraft",
    # "cogs.games.tcg.tcg",
    # "cogs.betting",
    # "cogs.music_test",
    # "cogs.reddit",
    # "cogs.message_history",
    # "cogs.deepfry",
    "cogs.fap",
    "cogs.games.blackjack"
)

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
else:
    print("No arguments provided!")
