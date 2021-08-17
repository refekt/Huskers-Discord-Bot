import asyncio
import pathlib
import random
import sys
from datetime import datetime, timedelta

import discord
import requests
from PIL import Image
from discord.ext.commands import Bot
from discord_slash import SlashCommand
from discord_slash.context import ComponentContext
from discord_slash.model import CallbackObject
from imgurpython import ImgurClient

from objects.Thread import send_reminder
from utilities.constants import CHAN_HOF_PROD, CHAN_SHAME, CHAN_SCOTTS_BOTS, GUILD_PROD
from utilities.constants import DT_TASK_FORMAT
from utilities.constants import IMGUR_CLIENT, IMGUR_SECRET
from utilities.constants import PROD_TOKEN, TEST_TOKEN
from utilities.constants import debugging
from utilities.embed import build_embed
from utilities.mysql import Process_MySQL, sqlRetrieveTasks

client = Bot(
    command_prefix="$",
    case_insensitive=True,
    description="Bot Frost version 3.0! Now with Slash Commands",
    intents=discord.Intents.all()
)

slash = SlashCommand(client, sync_commands=True)  # Sync required

client_percent = 0.0047


async def change_my_status():
    statuses = (
        "Husker football 24/7",
        "Nebraska beat Florida 62-24",
        "the Huskers give up 400 yards rushing to one guy",
        "a swing pass for -1 yards",
        "a missed field goal"
    )
    try:
        print("### Attempting to change status...")
        await client.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=random.choice(statuses)
            )
        )
        print(f"### ~~~ Successfully changed status")
    except (AttributeError, discord.HTTPException) as err:
        print("### ~~~ Unable to change status: " + str(err).replace("\n", " "))
    except:
        print(f"### ~~~ Unknown error!", sys.exc_info()[0])


async def change_my_nickname():
    nicks = (
        "Bot Frost",
        "Mario Verbotzco",
        "Adrian Botinez",
        "Bot Devaney",
        "Mike Rilbot",
        "Robo Pelini",
        "Devine Ozigbot",
        "Mo Botty",
        "Bot Moos",
        "Bot Diaco",
        "Rahmir Botson",
        "I.M. Bott",
        "Linux Phillips",
        "Dicaprio Bottle",
        "Bryce Botheart",
        "Jobot Chamberlain",
        "Bot Bando",
        "Shawn Botson",
        "Zavier Botts",
        "Jimari Botler",
        "Bot Gunnerson",
        "Nash Botmacher",
        "Botger Craig",
        "Dave RAMington",
        "MarLAN Lucky",
        "Rex Bothead",
        "Nbotukong Suh",
        "Grant Bostrom",
        "Ameer Botdullah",
        "Botinic Raiola",
        "Vince Ferraboto",
        "economybot",
        "NotaBot_Human",
        "psybot",
        "2020: the year of the bot",
        "bottech129",
        "deerebot129"
    )

    try:
        print("### Attempting to change nickname...")
        await client.user.edit(
            username=random.choice(nicks)
        )
        print(f"### ~~~ Successfully changed display name")
    except discord.HTTPException as err:
        err_msg = "### ~~~ Unable to change display name: " + str(err).replace("\n", " ")
        print(err_msg)
    except:
        print(f"### ~~~ Unknown error!", sys.exc_info()[0])


async def load_tasks():
    def convert_duration(value: str):
        imported_datetime = datetime.strptime(value, DT_TASK_FORMAT)
        now = datetime.now()

        if imported_datetime > now:
            duration = imported_datetime - now
            return duration
        return timedelta(seconds=0)

    async def convert_destination(destination_id: int):
        destination_id = int(destination_id)
        try:
            member = guild.get_member(destination_id)
            if member is not None:
                return member
        except:
            pass

        try:
            channel = guild.get_channel(destination_id)
            if channel is not None:
                return channel
        except:
            pass

        return None

    tasks = Process_MySQL(sqlRetrieveTasks, fetch="all")
    guild = client.guilds[0]

    if guild is None:
        print("### ~~~ Load tasks guild is none")
        return
    else:
        print(f"### ~~~ Guild == {guild}")

    if tasks is None:
        return print("### ;;; No tasks were loaded")

    print(f"### There are {len(tasks)} to be loaded")

    task_repo = []

    for task in tasks:
        send_when = convert_duration(task["send_when"])
        member_or_chan = await convert_destination(task["send_to"])

        if member_or_chan is None:
            print(f"### ;;; Skipping task because destination is None.")
            continue

        if task["author"] is None:
            task["author"] = "N/A"

        if send_when == timedelta(seconds=0):
            print(f"### ;;; Alert time already passed! {task['send_when']}")
            await send_reminder(
                thread_name=None,
                num_seconds=0,
                destination=member_or_chan,
                message=task["message"],
                source=task["author"],
                alert_when=task["send_when"]
            )
            continue

        task_repo.append(
            asyncio.create_task(
                send_reminder(
                    thread_name=str(member_or_chan.id + send_when.total_seconds()),
                    num_seconds=send_when.total_seconds(),
                    destination=member_or_chan,
                    message=task["message"],
                    source=task["author"],
                    alert_when=task["send_when"]
                )
            )
        )

    for index, task in enumerate(task_repo):
        await task


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
    for reaction in reactions:
        if reaction.message.channel.id in (CHAN_HOF_PROD, CHAN_SHAME):  # Stay out of HOF and HOS
            continue

        slowpoke_emoji = "<:slowpoke:758361250048245770>"
        server_member_count = len(client.users)
        reaction_threshold = int(client_percent * server_member_count)
        hos_channel = hof_channel = None

        if reaction.count >= reaction_threshold:
            print(f"### ~~~ Reaction threshold broken with [{reaction.count}] [{reaction.emoji}] reactions")
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
                if not hof:
                    embed_title = f"{slowpoke_emoji * 3} Hall of Shame Message {slowpoke_emoji * 3}"
                    embed_description = "Messages so shameful they had to be memorialized forever!"
                    channel = hos_channel
                else:
                    embed_title = f"{'🏆' * 3} Hall of Shame Message {'🏆' * 3}"
                    embed_description = "Messages so amazing they had to be memorialized forever!"
                    channel = hof_channel

                avatar_url = str(reaction.message.author.avatar_url).split("?")[0].replace("webp", "png")

                make_slowking(avatar_url)

                slowking_path = f"{pathlib.Path(__file__).parent.resolve()}\\resources\\images\\new_slowking.png"
                slowking_path = upload_picture(slowking_path)

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


@client.event
async def on_connect():
    await change_my_status()
    await change_my_nickname()
    await load_tasks()


@client.event
async def on_ready():
    print(
        f"### Bot Frost version 3.0 ###\n"
        f"### ~~~ Name: {client.user}\n"
        f"### ~~~ ID: {client.user.id}\n"
        f"### ~~~ Guild: {client.guilds[0]}\n"
        f"### ~~~ HOF/HOS Reaction Threshold: {int(len(client.users) * client_percent)}\n"
        f"### The bot is ready!"
    )

    if debugging():
        return

    bot_spam = client.get_channel(CHAN_SCOTTS_BOTS)
    embed = build_embed(
        title="Bot Frost Online",
        description=f"I'm online as {client.user.mention}",
        fields=[
            ["Info", "I was restarted, but now I'm back!"]
        ]
    )
    await bot_spam.send(embed=embed)


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if debugging() and not payload.member.id == 189554873778307073:
        return
    else:
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

    await hall_of_fame_messages(message.reactions)


@client.event
async def on_slash_command(ctx):
    pass


    # @client.event
    # async def on_slash_command_error(ctx, ex):
    #     if debugging():
    #         return
    #
    #     embed = build_embed(
    #         title="Slash Command Error",
    #         fields=[
    #             ["Description", str(ex)]
    #         ]
    #     )
    #     await ctx.send(embed=embed, hidden=True)


@client.event
async def on_component(ctx: ComponentContext):
    """ Called when a component is triggered. """
    pass


@client.event
async def on_component_callback(ctx: ComponentContext, callback: CallbackObject):
    pass


if debugging():
    token = TEST_TOKEN
else:
    token = PROD_TOKEN

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
    print(f"### ~~~ Loading extension: {extension}")
    client.load_extension(extension)

client.run(token)
