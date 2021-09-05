import asyncio
import pathlib
import platform
import random
import sys
import traceback
import typing
from datetime import (
    datetime,
    timedelta
)

import discord
import requests
import tweepy
from PIL import Image
from discord.ext.commands import Bot
from discord_slash import (
    ButtonStyle,
    ComponentContext,
    SlashCommand
)
from discord_slash.context import (
    SlashContext
)
from discord_slash.utils.manage_components import (
    create_actionrow,
    create_button
)
from imgurpython import ImgurClient

from objects.Thread import (
    send_reminder,
    TwitterStreamListener
)
from utilities.constants import (
    CHAN_GENERAL,
    CHAN_HOF_PROD,
    CHAN_RECRUITING,
    CHAN_RULES,
    CHAN_SCOTTS_BOTS,
    CHAN_SHAME,
    CHAN_TWITTERVERSE,
    CommandError,
    DT_TASK_FORMAT,
    DT_TWEET_FORMAT,
    GEE_USER,
    IMGUR_CLIENT,
    IMGUR_SECRET,
    PROD_TOKEN,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_KEY,
    TWITTER_SECRET_KEY,
    TWITTER_TOKEN,
    TWITTER_TOKEN_SECRET,
    UserError,
    set_component_key
)
from utilities.embed import build_embed
from utilities.mysql import (
    Process_MySQL,
    sqlRetrieveTasks
)

client = Bot(
    command_prefix="$",
    case_insensitive=True,
    description="Bot Frost version 3.0! Now with Slash Commands",
    intents=discord.Intents.all()
)

slash = SlashCommand(client, sync_commands=True)  # Sync required
client_percent = 0.0047
list_members = []


def log(message: str, level: int):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ {message}")


def current_guild() -> typing.Union[discord.Guild, None]:
    if len(client.guilds) == 0:
        log(f"Unable to find any guilds!", 1)
        return None
    else:
        log(f"Active Guilds: {[guild.name for guild in client.guilds]}", 1)
        return client.guilds[0]


async def change_my_status():
    statuses = (
        "Husker football 24/7",
        "Nebraska beat Florida 62-24",
        "the Huskers give up 400 yards rushing to one guy",
        "a swing pass for -1 yards",
        "a missed field goal"
    )
    try:
        log(f"Attempting to change status...", 0)
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=random.choice(statuses)
            )
        )
        log(f"Successfully changed status", 1)
    except (AttributeError, discord.HTTPException) as err:
        log(f"Unable to change status: " + str(err).replace('\n', ' '), 1)
    except:
        log(f"Unknown error!" + str(sys.exc_info()[0]), 0)


async def load_tasks():
    def convert_duration(value: str):
        imported_datetime = datetime.strptime(value, DT_TASK_FORMAT)
        now = datetime.now()

        if imported_datetime > now:
            duration = imported_datetime - now
            return duration
        return timedelta(seconds=0)

    async def convert_destination(cur_guild, destination_id: int):
        destination_id = int(destination_id)
        try:
            member = cur_guild.get_member(destination_id)
            if member is not None:
                return member
        except:
            pass

        try:
            channel = cur_guild.get_channel(destination_id)
            if channel is not None:
                return channel
        except:
            pass

        return None

    tasks = Process_MySQL(sqlRetrieveTasks, fetch="all")

    guild = current_guild()
    if guild is None:
        loop = asyncio.get_event_loop()
        loop.stop()
        await client.close()
        log(f"Unable to find any guilds. Exiting...", 1)
    else:
        log(f"Guild == {guild}", 1)
    if tasks is None:
        return log(f"No tasks were loaded", 1)

    log(f"There are {len(tasks)} to be loaded", 0)

    task_repo = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    for task in tasks:
        send_when = convert_duration(task["send_when"])
        destination = await convert_destination(guild, task["send_to"])

        if destination is None:
            log(f"Skipping task because destination is None.", 1)
            continue

        if task["author"] is None:
            task["author"] = "N/A"

        if send_when == timedelta(seconds=0):
            log(f"Alert time already passed! {task['send_when']}", 1)
            await send_reminder(
                num_seconds=0,
                destination=destination,
                message=task["message"],
                source=task["author"],
                alert_when=task["send_when"],
                missed=True
            )
            continue

        task_repo.append(
            asyncio.create_task(
                send_reminder(
                    num_seconds=send_when.total_seconds(),
                    destination=destination,
                    message=task["message"],
                    source=task["author"],
                    alert_when=task["send_when"]
                )
            )
        )

    for index, task in enumerate(task_repo):
        await task


async def send_tweet_alert(message: str):
    log(f"Receiving Twitter alert", 0)
    log(f"Twttier Alert: {message}", 1)
    chan_twitter: discord.TextChannel = client.get_channel(id=CHAN_TWITTERVERSE)

    embed = build_embed(
        fields=[
            ["Twitter Stream Listener Alert", message]
        ]
    )
    await chan_twitter.send(embed=embed)


async def send_tweet(tweet):
    if tweet.author.id_str not in [member["id_str"] for member in list_members]:
        return

    direct_url = f"https://twitter.com/{tweet.author.screen_name}/status/{tweet.id_str}/"

    if hasattr(tweet, "extended_tweet"):
        fields = [
            ["Message", tweet.extended_tweet["full_text"]]
        ]
    else:
        fields = [
            ["Message", tweet.text]
        ]

    embed = build_embed(
        url="https://twitter.com/i/lists/1307680291285278720",
        fields=fields,
        footer=f"Tweet sent {tweet.created_at.strftime(DT_TWEET_FORMAT)}"
    )

    embed.set_author(
        name=f"{tweet.author.name} (@{tweet.author.screen_name}) via {tweet.source}",
        icon_url=tweet.author.profile_image_url_https
    )

    if hasattr(tweet, "extended_entities"):
        try:
            for index, media in enumerate(tweet.extended_entities["media"]):
                if index == 0:
                    embed.set_image(
                        url=tweet.extended_entities["media"][index]["media_url"]
                    )
                embed.add_field(
                    name=f"Media #{index + 1}",
                    value=f"[Link #{index + 1}]({media['media_url']})",
                    inline=False
                )
        except:
            pass

    log(f"Sending tweeit from @{tweet.author.screen_name}", 1)
    chan_twitter: discord.TextChannel = client.get_channel(id=CHAN_TWITTERVERSE)

    buttons = [
        create_button(
            style=ButtonStyle.gray,
            custom_id=f"{set_component_key()}_send_to_general",
            label="Send to General"
        ),
        create_button(
            style=ButtonStyle.gray,
            custom_id=f"{set_component_key()}_send_to_recruiting",
            label="Send to Recruiting"
        ),
        create_button(
            style=ButtonStyle.URL,
            label="Open Tweet",
            url=direct_url
        )
    ]
    actionrow = create_actionrow(*buttons)
    # noinspection PyArgumentList
    await chan_twitter.send(embed=embed, components=[actionrow])


def start_twitter_stream():
    listener = TwitterStreamListener(send_tweet, send_tweet_alert, client.loop)
    auth = tweepy.OAuthHandler(
        consumer_key=TWITTER_KEY,
        consumer_secret=TWITTER_SECRET_KEY
    )
    auth.set_access_token(
        key=TWITTER_TOKEN,
        secret=TWITTER_TOKEN_SECRET
    )
    api = tweepy.API(auth_handler=auth)
    stream = tweepy.Stream(
        auth=api.auth,
        listener=listener
    )

    for member in tweepy.Cursor(api.list_members, list_id=TWITTER_HUSKER_MEDIA_LIST_ID).items():
        list_members.append(
            {
                "screen_name": member.screen_name,
                "id_str": member.id_str,

            }
        )
    if "Windows" in platform.platform():
        list_members.append(
            {
                "screen_name": "ayy_gbr",
                "id_str": "15899943",

            }
        )
    stream.filter(
        follow=[member["id_str"] for member in list_members],
        is_async=True
    )


def upload_picture(path: str) -> str:
    imgur_client = ImgurClient(IMGUR_CLIENT, IMGUR_SECRET)
    url = imgur_client.upload_from_path(
        path=path,
        config=None,
        anon=True
    )

    return url.get("link", None)


def make_slowking(avatar_url):
    avatar_img = Image.open(requests.get(avatar_url, stream=True).raw)

    base_img_path = "resources/images/slowking.png"
    base_img = Image.open(base_img_path)

    paste_pos = (262, 262)
    base_img.paste(avatar_img, paste_pos, avatar_img)
    base_img.save("resources/images/new_slowking.png", "PNG")


async def hall_of_fame_messages(reactions: list):
    multiple_threshold = False
    for reaction in reactions:
        if multiple_threshold:  # Rare instance where a message has multiple reactions that break the threshold
            break

        if reaction.message.channel.id in (CHAN_HOF_PROD, CHAN_SHAME):  # Stay out of HOF and HOS
            continue

        slowpoke_emoji = "<:slowpoke:758361250048245770>"
        server_member_count = len(client.users)
        reaction_threshold = int(client_percent * server_member_count)
        hos_channel = hof_channel = None

        if reaction.count >= reaction_threshold:
            multiple_threshold = True
            log(f"Reaction threshold broken with [{reaction.count}] [{reaction.emoji}] in [{reaction.message.channel}] reactions", 0)
            if str(reaction.emoji) == slowpoke_emoji:
                hof = False
                hos_channel = client.get_channel(id=CHAN_SHAME)
                raw_message_history = await hos_channel.history(limit=5000).flatten()
            else:
                hof = True
                hof_channel = client.get_channel(id=CHAN_HOF_PROD)
                raw_message_history = await hof_channel.history(limit=5000).flatten()

            duplicate = False
            for raw_message in raw_message_history:
                if len(raw_message.embeds) > 0:
                    if str(reaction.message.id) in raw_message.embeds[0].footer.text:
                        duplicate = True
                        break
            del raw_message_history

            if not duplicate:
                slowking_path = None

                if not hof:
                    embed_title = f"{slowpoke_emoji * 3} Hall of Shame Message {slowpoke_emoji * 3}"
                    embed_description = "Messages so shameful they had to be memorialized forever!"
                    channel = hos_channel

                    avatar_url = str(reaction.message.author.avatar_url).split("?")[0].replace("webp", "png")
                    make_slowking(avatar_url)
                    slowking_path = f"{pathlib.Path(__file__).parent.resolve()}\\resources\\images\\new_slowking.png"
                    slowking_path = upload_picture(slowking_path)
                else:
                    embed_title = f"{'🏆' * 3} Hall of Fame Message {'🏆' * 3}"
                    embed_description = "Messages so amazing they had to be memorialized forever!"
                    channel = hof_channel

                embed = build_embed(
                    title=embed_title,
                    description=embed_description,
                    thumbnail=slowking_path if not None else None,
                    fields=[
                        ["Author", reaction.message.author.mention],
                        ["Message", reaction.message.content],
                        ["Message Link", f"[Click to view message]({reaction.message.jump_url})"]
                    ],
                    footer=f"Message ID: {reaction.message.id} | Hall of Shame message created at {reaction.message.created_at.strftime('%B %d, %Y at %H:%M%p')}"
                )
                await channel.send(embed=embed)
                log(f"Processed HOF/HOS message.", 0)


async def send_welcome_message(who: discord.Member):
    chan_rules = client.get_channel(CHAN_RULES)

    embed = build_embed(
        title="Welcome to the server!",
        description="The official Husker football discord server",
        thumbnail="https://cdn.discordapp.com/icons/440632686185414677/a_061e9e57e43a5803e1d399c55f1ad1a4.gif",
        fields=[
            ["Rules", f"Please be sure to check out {chan_rules.mention if chan_rules is not None else 'the rules channel'} to catch up on server rules."],
            ["Commands", f"View the list of commands with the `/commands` command. Note: commands only work while in the server."],
            ["Roles", "You can assign yourself come flair by using the `/roles` command."]
        ]
    )

    await who.send(embed=embed)


@client.event
async def on_connect():
    if "Windows" not in platform.platform():
        start_twitter_stream()


@client.event
async def on_ready():
    threshold = int(len(client.users) * client_percent)

    log(f"Bot Frost version 3.0", 0)
    log(f"Name: {client.user}", 1)
    log(f"ID: {client.user.id}", 1)
    log(f"Guild: {current_guild()}", 1)
    log(f"HOF/HOS Reaction Threshold: {threshold}", 1)
    log(f"The bot is ready!", 0)

    if "Windows" not in platform.platform():
        try:
            changelog_path = None

            if "Windows" in platform.platform():
                log(f"Windows changelog", 1)
                changelog_path = pathlib.PurePath(f"{pathlib.Path(__file__).parent.resolve()}/changelog.md")
            elif "Linux" in platform.platform():
                log(f"Linxue changelog", 0)
                changelog_path = pathlib.PurePosixPath(f"{pathlib.Path(__file__).parent.resolve()}/changelog.md")

            changelog = open(changelog_path, "r")
            lines = changelog.readlines()
            lines_str = ""

            for line in lines:
                lines_str += f"* {str(line)}"
        except OSError:
            lines_str = "Error loading changelog."

        bot_spam = client.get_channel(CHAN_SCOTTS_BOTS)
        embed = build_embed(
            title="Husker Discord Bot",
            fields=[
                ["Info", f"I was restarted, but now I'm back! I'm now online as {client.user.mention}! Check out /commands."],
                ["HOF/HOS Reaction Threshold", f"{threshold}"],
                ["Changelog", lines_str],
                ["More Changelog", f"[View rest of commits](https://github.com/refekt/Bot-Frost/commits/master)"]
            ]
        )
        await bot_spam.send(embed=embed)

        await change_my_status()
        await load_tasks()


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    channel = client.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    await hall_of_fame_messages(message.reactions)


@client.event
async def on_member_join(member: discord.Member):
    log(f"New Member: {member.display_name}", 0)
    await send_welcome_message(member)


@client.event
async def on_component(ctx: ComponentContext):
    if ("send_to_general" in ctx.custom_id) or ("send_to_recruiting" in ctx.custom_id):
        await ctx.defer(hidden=True)
        chan: typing.Union[discord.TextChannel, None] = None
        if "send_to_general" in ctx.custom_id:
            chan = ctx.bot.get_channel(id=CHAN_GENERAL)
        elif "send_to_recruiting" in ctx.custom_id:
            chan = ctx.bot.get_channel(id=CHAN_RECRUITING)
        if chan is not None:
            twitter_url = ctx.origin_message.components[0]["components"][2]["url"]
            await chan.send(f"{ctx.author.mention} forwarded: {twitter_url}")
            await ctx.send(f"Sent to {chan.mention}!", hidden=True)


if "Windows" not in platform.platform():
    @client.event
    async def on_slash_command_error(ctx: SlashContext, ex: Exception):
        def format_traceback(tback: list):
            return "".join(tback).replace("Aaron", "Secret")

        embed = None
        if isinstance(ex, discord.errors.NotFound):
            return log(f"Skipping a NotFound error", 1)
        elif isinstance(ex, UserError):
            embed = build_embed(
                title="Husker Bot User Error",
                description="An error occured with user input",
                fields=[
                    ["Error Message", ex.message]
                ]
            )
        elif isinstance(ex, CommandError):
            embed = build_embed(
                title="Husker Bot Command Error",
                description="An error occured with command processing",
                fields=[
                    ["Error Message", ex.message]
                ]
            )
        else:
            embed = build_embed(
                title="Husker Bot Command Error",
                description="An unknown error occured",
                fields=[
                    ["Error Message", f"{ex.__class__}: {ex}"]
                ]
            )

        await ctx.send(embed=embed)

        traceback_raw = traceback.format_exception(
            etype=type(ex),
            value=ex,
            tb=ex.__traceback__
        )

        tback = format_traceback(traceback_raw)
        cmd = ctx.command
        sub_cmd = ""
        if ctx.subcommand_name is not None:
            sub_cmd = ctx.subcommand_name

        inputs = []

        for key, value in ctx.data.items():
            inputs.append(f"{key} = {value}")

        message = f"{ctx.author.mention} ({ctx.author.display_name}, {ctx.author_id}) received an unknown error!\n" \
                  f"\n" \
                  f"`/{cmd}{' ' + sub_cmd if sub_cmd is not None else ''} {inputs}`\n" \
                  f"\n" \
                  f"```\n{tback}\n```"

        try:
            gee = client.get_user(id=GEE_USER)
            await gee.send(content=message)
        except:
            await ctx.send(content=f"<@{GEE_USER}>\n{message}")

extensions = [
    "commands.croot_bot",
    "commands.admin",
    "commands.text",
    "commands.image",
    "commands.football_stats",
    "commands.reminder",
    # "commands.testing"
]
for extension in extensions:
    log(f"Loading extension: {extension}", 1)
    client.load_extension(extension)

client.run(PROD_TOKEN)
