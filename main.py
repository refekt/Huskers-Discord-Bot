import sys

import discord
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from utilities.constants import TEST_TOKEN, PROD_TOKEN
from utilities.constants import production_server
from utilities.embed import build_embed

client = Bot(
    command_prefix="$",
    case_insensitive=True,
    description="Bot Frost version 3.0! Now with Slash Commands",
    intents=discord.Intents.all()
)

slash = SlashCommand(client, sync_commands=True)  # Sync required


# Tried, but there's no easy way to extract direct links to share.
# class SocialMediaURLType:
#     tiktok = "tiktok.com"
#     facebook = "facebook.com"
#     none = None
#     search_string = r"(vm\.tiktok\.com\/.{0,}\/|facebook\.com\/\d{0,}\/videos\/\d{0,})"
#
#
# def SocialMediaURL(message: discord.Message) -> list:
#     matches = re.findall(SocialMediaURLType.search_string, message.clean_content)
#
#     for match in matches:
#         if not matches:
#             return SocialMediaURLType.none
#         elif SocialMediaURLType.tiktok in match:
#             url = f"https://{match}"
#             shortened_req = requests.get(url, headers=HEADERS)
#             redirected_req = requests.get(shortened_req.url, headers=HEADERS)
#             video_regex = r"https:\/\/.{0,}\.tiktok\.com\/video\/.{0,}vr\="
#             soup = BeautifulSoup(redirected_req.content, "html.parser")
#             url_find = re.findall(video_regex, soup.text)
#
#             embed_image = soup.find_all(text=re.compile(video_regex))
#         elif SocialMediaURLType.facebook in match:
#             pass
#
#
# def _hasSocialMediaEmbed(message: discord.Message) -> bool:
#     matches = re.findall(SocialMediaURLType.search_string, message.clean_content)
#
#     if matches:
#         return True
#     else:
#         return False


@client.event
async def on_ready():
    print(
        f"### Bot Frost version 3.0 ###\n"
        f"### ~~~ Name: {client.user}\n"
        f"### ~~~ ID: {client.user.id}\n"
        f"### The bot is ready! ###"
    )


@client.event
async def on_connect():
    pass


@client.event
async def on_raw_reaction_add(payload):
    pass


@client.event
async def on_raw_reaction_remove(payload):
    pass


@client.event
async def on_member_join(member):
    pass


@client.event
async def on_error(event, *args, **kwargs):
    # print(event, args, kwargs)
    pass


@client.event
async def on_message(message):
    # if message.author.bot:
    #     return
    #
    # if len(message.embeds) > 0:
    #     return
    #
    # if _hasSocialMediaEmbed(message):
    #     sm_url = SocialMediaURL(message)
    pass


@client.event
async def on_slash_command_error(ctx, ex):
    embed = build_embed(
        title="Slash Command Error",
        fields=[
            ["Description", ex]
        ]
    )
    await ctx.send(embed=embed, hidden=True)


token = None

if len(sys.argv) > 0:
    if production_server():
        token = PROD_TOKEN
    else:
        token = TEST_TOKEN

extensions = [
    "commands.croot_bot",
    "commands.admin",
    "commands.text",
    "commands.image",
    "commands.football_stats"
    # "commands.testing"
]
for extension in extensions:
    print(f"### ~~~ Loading extension: {extension} ###")
    client.load_extension(extension)

client.run(token)
