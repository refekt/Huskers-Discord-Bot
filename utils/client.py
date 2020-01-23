import traceback
import hashlib
import json
import logging
import random
import re
import sys
from datetime import datetime

import discord
from discord.ext import commands

import utils.consts as consts
from utils.consts import chan_HOF_prod, chan_HOF_test, chan_botlogs, chan_dbl_war_room, chan_war_room, chan_scott
from utils.consts import change_my_nickname, change_my_status
from utils.consts import establish_logger, print_log
from utils.consts import role_gumby, role_potato, role_asparagus, role_airpod, role_isms, role_meme, role_packer, role_pixel, role_runza, role_minecraft
from utils.embed import build_embed
from utils.misc import on_prod_server
from utils.mysql import process_MySQL, sqlLogError, sqlDatabaseTimestamp, sqlLogUser


async def split_payload(payload):
    p = dict()
    p["channel_id"] = client.get_channel(payload.channel_id)
    p["emoji"] = payload.emoji
    p["guild_id"] = client.get_guild(payload.guild_id)
    p["user_id"] = client.get_user(payload.user_id)
    c = await client.fetch_channel(payload.channel_id)
    p["message"] = await c.fetch_message(payload.message_id)

    del c
    del payload

    return p


async def process_error(ctx, error):
    err = getattr(error, "original", error)

    if isinstance(err, commands.CommandNotFound):
        return

    elif isinstance(err, commands.BadArgument):
        return await ctx.send(f"Command `{client.command_prefix}{ctx.command.qualified_name}` received a bad argument. Review `{client.command_prefix}help {ctx.command.qualified_name}` for more "
                              f"information.")

    elif isinstance(err, discord.ext.commands.CommandOnCooldown):
        return await ctx.send(f"HOLD UP {ctx.message.author.mention}! ${ctx.command.qualified_name} is cooling down. {str(error).split('.')[1]} seconds.")

    elif isinstance(err, (discord.ext.commands.MissingRole, discord.ext.commands.MissingAnyRole)):
        return await ctx.send(f"{ctx.message.author.mention}! You are not authorized to use this command!")

    elif isinstance(err, (discord.ext.commands.CommandInvokeError, discord.ext.commands.UserInputError)):
        return await ctx.send(f"{err}")

    elif isinstance(err, discord.ext.commands.NoPrivateMessage):
        return await ctx.send(f"The command `{client.command_prefix}{ctx.command.qualified_name}` cannot be used in private messages.")

    else:
        try:
            output_msg = f"Whoa there, {ctx.message.author.mention}! Something went doesn't look quite right. Please review `$help` for further assistance. Contact my creators if the problem continues.\n" \
                         f"```" \
                         f"Message ID: {ctx.message.id}\n" \
                         f"Channel: {ctx.message.channel.name} / {ctx.message.channel.id}\n" \
                         f"Author: {ctx.message.author}\n" \
                         f"Content: {ctx.message.content}\n" \
                         f"Error: {error}" \
                         f"```"
            await ctx.send(output_msg)
        except:
            await ctx.send("Unknown error happened!")

    process_MySQL(query=sqlLogError, values=(f"{ctx.author.name}#{ctx.author.discriminator}", [err for err in error.args]))


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

        if re.search(r"f{1,}u{1,}c{1,}k{1,}.{0,}[\W](y{1,}o{1,}u{1,}|u{1,}).{0,}[\W]b{1,}o{1,}t{1,}", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="BITE MY SHINY, METAL ASS",
                    image=random.choice(myass)
                ),
                content=message.author.mention
            )

        if re.search(r"l{1,}o{1,}v{1,}e{1,}.{0,}[\W](y{1,}o{1,}u{1,}|u{1,}).{0,}[\W]b{1,}o{1,}t{1,}", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="Shut Up Baby, I Know It",
                    image="https://media1.tenor.com/images/c1fd95af4433edf940fdc8d08b411622/tenor.gif?itemid=7506108"
                ),
                content=message.author.mention
            )

        if re.search(r"g{1,}o{1,}o{1,}d{1,}.{0,}[\W]b{1,}o{1,}t{1,}", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="😝",
                    image="https://i.imgur.com/52v1upi.png"
                ),
                content=message.author.mention
            )

        if re.search(r"b{1,}a{1,}d{1,}.{0,}[\W]b{1,}o{1,}t{1,}", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="╰（‵□′）╯",
                    image="https://i.redd.it/6vznew4w92211.jpg"
                ),
                content=message.author.mention
            )

        if re.search(r"(should|could|would|might)\sof", message.content, re.IGNORECASE):
            await channel.send(
                embed=build_embed(
                    title="Grammar Police",
                    fields=[
                        ["Fix yourself!", "~~of~~ have*"],
                        ["Not My Idea", "This was <@440885775132000266>'s idea!"]
                    ]
                )
            )

        if "isms" in message.content.lower():
            if random.random() >= .90:
                await message.channel.send("Isms? That no talent having, no connection having hack? All he did was lie and make **shit** up for fake internet points. I'm glad he's gone.")

        if not type(channel) == discord.DMChannel and role_gumby in [roleid.id for roleid in message.author.roles]:
            # blocked = False
            try:
                if not message.author.is_blocked():
                    await message.add_reaction("🦐")
                else:
                    print(f"Unable to add 🦐 reaction to {message.author}'s message because I am blocked by them!")
            except discord.Forbidden:
                print(f"Unable to add 🦐 reaction to {message.author}'s message. They most likely blocked me!")

            if random.random() >= .99:
                await message.channel.send("https://i.imgur.com/1tVJ2tW.gif")

    async def find_subreddits():
        subreddits = re.findall(r'(?:^| )(/?r/[a-z]+)', message.content.lower())

        if len(subreddits) > 0:
            subs = []

            for s in subreddits:
                if "huskers" in s or "cfb" in s:
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

    await auto_replies()
    await find_subreddits()
    await add_votes()


async def monitor_reactions(channel, emoji, user, message):
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

    await trivia_message()


async def hall_of_fame_messages(reactions: list):
        chan = client.get_channel(id=chan_HOF_prod)

        if chan is None:
            chan = client.get_channel(id=chan_HOF_test)

        banned_channels = (chan_dbl_war_room, chan_war_room, chan_botlogs)

        if chan.id in banned_channels:
            return

        pinned_messages = []
        message_history_raw = []
        duplicate = False

        def server_member_count():
            return len(client.users)

        threshold = int(0.0075 * server_member_count())

        for reaction in reactions:
            if reaction.count >= threshold and not reaction.message.channel.name == chan.name and not ".addvotes" in reaction.message.content:
                if not reaction.message.author.bot:
                    message_history_raw = await chan.history(limit=5000).flatten()

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
                        await chan.send(embed=embed)

        del message_history_raw
        del pinned_messages
        del duplicate


async def roles_message(action, message: discord.Message, member: discord.User, emoji: discord.Emoji):
    roles_title = "Huskers' Discord Roles"
    try:
        if message.embeds[0].title == roles_title:
            guild = client.get_guild(440632686185414677)
            member = guild.get_member(member.id)
            roles = {
                "🥔": guild.get_role(role_potato),
                "💚": guild.get_role(role_asparagus),
                "🥪": guild.get_role(role_runza),
                "😹": guild.get_role(role_meme),
                "♣": guild.get_role(role_isms),
                "🧀": guild.get_role(role_packer),
                "☎": guild.get_role(role_pixel),
                "🎧": guild.get_role(role_airpod),
                "🪓": guild.get_role(role_minecraft)
            }

            if not emoji.name in [emoji for emoji in roles.keys()]:
                return

            if action == "add":
                await member.add_roles(roles[emoji.name], reason=roles_title)
            elif action == "remove":
                await member.remove_roles(roles[emoji.name], reason=roles_title)
    except IndexError:
        pass


class MyClient(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

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
                    channel = client.get_channel(chan_war_room)
                elif context[2].lower() == "scott":
                    channel = client.get_channel(chan_scott)
                else:
                    await ctx.message.author.send(error_message)
                    return

                if checkID.hexdigest() == mammals[context[1]]:
                    context_commands = f"{context[0]} {context[1]} {context[2]}"
                    message = ctx.message.content[len(context_commands):]

                    embed = discord.Embed(title="Secret Mammal Messaging System (SMMS)", color=0xD00000)
                    embed.set_thumbnail(url="https://i.imgur.com/EGC1qNt.jpg")
                    embed.add_field(name="Back Channel Communications", value=message)

                    await channel.send(embed=embed)
                else:
                    await ctx.message.author.send("Shit didn't add up")
                    return
            except:
                await process_error(ctx, error)
        else:
            await process_error(ctx, error)

    async def on_connect(self):
        process_MySQL(query=sqlDatabaseTimestamp, values=(client.user.display_name, True, str(datetime.utcnow()).split(".")[0]))

    async def on_disconnect(self):
        process_MySQL(query=sqlDatabaseTimestamp, values=(f"{client.user}", False, str(datetime.utcnow()).split(".")[0]))

    async def on_ready(self):
        appinfo = await self.application_info()

        await change_my_status(client)
        await change_my_nickname(client, ctx=None)

        print(
            f"### Bot Frost version 2.0 ###\n"
            f"### ~~~ Name: {client.user}\n"
            f"### ~~~ ID: {client.user.id}\n"
            f"### ~~~ Description: {appinfo.description}\n"
            f"### ~~~ Onwer Name: {appinfo.owner.name}#{appinfo.owner.discriminator}\n"
            f"### ~~~ Owner ID: {appinfo.owner.id}\n"
            f"### ~~~ Owner Created: {appinfo.owner.created_at}\n"
            f"### ~~~ Latency: {self.latency * 1000:.2f} MS\n"
            f"### ~~~ Command Prefix: \"{self.command_prefix}\""
        )

        # establish_logger(category=logging.ERROR)

        # print_log(logging.ERROR, "Testing!")

    async def on_resume(self, ctx):
        pass

    async def on_message(self, message):

        await monitor_messages(message)

        await self.process_commands(message)  # Always needed to process commands

    async def on_message_delete(self, message):
        pass

    async def on_bulk_message_delete(self, message):
        pass

    async def on_raw_message_delete(self, payload):
        pass

    async def on_raw_bulk_message_delete(self, payload):
        pass

    async def on_message_edit(self, before, after):
        pass

    async def on_raw_message_edit(self, payload):
        pass

    async def on_reaaction_add(reaction, user):
        pass

    async def on_raw_reaction_add(self, payload):
        payload = await split_payload(payload)

        await monitor_reactions(channel=payload["channel_id"], emoji=payload["emoji"], user=payload["user_id"], message=payload["message"])
        await hall_of_fame_messages(payload["message"].reactions)
        await roles_message(action="add", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])

    async def on_reaction_remove(reaction, user):
        pass

    async def on_raw_reaction_remove(self, payload):
        payload = await split_payload(payload)

        await roles_message(action="remove", message=payload["message"], member=payload["user_id"], emoji=payload["emoji"])

    async def on_reaction_clear(self, message, reactions):
        pass

    async def on_raw_reaction_clear(self, payload):
        pass

    async def on_member_join(self, member):
        process_MySQL(query=sqlLogUser, values=(f"{member.name}#{member.discriminator}", "member_join", "N/A"))

    async def on_member_remove(self, member):
        process_MySQL(query=sqlLogUser, values=(f"{member.name}#{member.discriminator}", "remove", "N/A"))

    async def on_member_update(self, before, after):
        pass

    async def on_user_udpate(self, before, after):
        process_MySQL(query=sqlLogUser, values=(f"{before.name}#{before.discriminator}", "user_update", await compare_users(before, after)))

    async def on_member_ban(self, guild, user):
        process_MySQL(query=sqlLogUser, values=(f"{user.name}#{user.discriminator}", "ban", "N/A"))

    async def on_member_unban(self, guild, user):
        process_MySQL(query=sqlLogUser, values=(f"{user.name}#{user.discriminator}", "unban", "N/A"))


command_prefix = "$"

if sys.argv[1] == "test":
    command_prefix = "%"

client = MyClient(command_prefix=command_prefix)
extensions = ("cogs.admin", "cogs.flags", "cogs.images", "cogs.referee", "cogs.schedule", "cogs.text", "cogs.croot", "cogs.games.trivia", "cogs.games.minecraft", "cogs.betting")  #reddit

for extension in extensions:
    try:
        client.load_extension(extension)
        print(f"### Successfully loaded [{extension}] commands! ###")
    except:
        traceback.print_exc()

if len(sys.argv) > 0:
    if on_prod_server():
        token = consts.prod_token
        client.run(token)
    else:
        token = consts.test_token
        client.run(token)
else:
    print("No arguments provided")
