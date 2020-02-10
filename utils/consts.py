import discord
import os
import platform
import random
import sys

import pytz
from discord.ext.commands import BucketType
from dotenv import load_dotenv

import logging

print(f"### Platform == {platform.platform()} ###")

if "Windows" in platform.platform():
    print("### Windows environment set ###")
    load_dotenv(dotenv_path="variables.env")
elif "Linux" in platform.platform():
    if sys.argv[1] == "prod":
        print("### Production environment set ###")
        load_dotenv(dotenv_path="/home/botfrost/bot/variables.env")
    elif sys.argv[1] == "test":
        print("### Test environment set ###")
        load_dotenv(dotenv_path="/home/botfrost/bot/variables.env")
else:
    print(f"Unknown Platform: {platform.platform()}")

# Cooldown rates for commands
CD_GLOBAL_RATE = os.getenv("global_rate")
CD_GLOBAL_PER = os.getenv("global_per")
CD_GLOBAL_TYPE = BucketType.user

# Discord Bot Tokens
TEST_TOKEN = os.getenv("TEST_TOKEN")
PROD_TOKEN = os.getenv("DISCORD_TOKEN")
BACKUP_TOKEN = os.getenv("BACKUP_TOKEN")

# SQL information
SQL_HOST = os.getenv("sqlHost")
SQL_USER = os.getenv("sqlUser")
SQL_PASSWD = os.getenv("sqlPass")
SQL_DB = os.getenv("sqlDb")

# Reddit Bot Info
REDDIT_CLIENT_ID = os.getenv("reddit_client_id")
REDDIT_SECRET = os.getenv("reddit_secret")
REDDIT_PW = os.getenv("reddit_pw")

# SSH Information
SSH_HOST = os.getenv("ssh_host")
SSH_USER = os.getenv("ssh_user")
SSH_PW = os.getenv("ssh_pw")

# print("* ", _global_rate, _global_per, _global_type, test_token, prod_token, backup_token, host, user, passwd, db, reddit_client_id, reddit_secret, reddit_pw, ssh_host, ssh_user, ssh_pw,
# sep="\n* ", end="\n\n")

# Headers for `requests`
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'}

# Consistent timezone
TZ = pytz.timezone("US/Central")

# Discord Roles
ROLE_ADMIN_PROD = 440639061191950336
ROLE_ADMIN_TEST = 606301197426753536
ROLE_MOD_PROD = 443805741111836693
ROLE_POTATO = 583842320575889423
ROLE_ASPARAGUS = 583842403341828115
ROLE_LILRED = 464903715854483487
ROLE_RUNZA = 485086088017215500
ROLE_MEME = 448690298760200195
ROLE_ISMS = 592425861534449674
ROLE_PACKER = 609409451836964878
ROLE_PIXEL = 633698252809699369
ROLE_AIRPOD = 633702209703378978
ROLE_GUMBY = 459569717430976513
ROLE_MINECRAFT = 661409899481268238

# Discord Channels
CHAN_HOF_PROD = 487431877792104470
CHAN_HOF_TEST = 606655884340232192
CHAN_DBL_WAR_ROOM = 538419127535271946
CHAN_WAR_ROOM = 525519594417291284
CHAN_BOTLOGS = 458474143403212801
CHAN_SCOTT = 507520543096832001
CHAT_RULES = 651523695214329887
CHAN_RADIO_PROD = 660610967733796902
CHAN_RADIO_TEST = 595705205069185050

# Servers/guilds
GUILD_PROD = 440632686185414677
GUILD_TEST = 595705205069185045
# bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]


async def change_my_nickname(client, ctx):
    nicks = ("Bot Frost", "Mario Verbotzco", "Adrian Botinez", "Bot Devaney", "Mike Rilbot", "Robo Pelini", "Devine Ozigbot", "Mo Botty", "Bot Moos", "Luke McBotfry", "Bot Diaco", "Rahmir Botson",
             "I.M. Bott", "Linux Phillips", "Dicaprio Bottle", "Bryce Botheart", "Jobot Chamberlain", "Bot Bando", "Shawn Botson", "Zavier Botts", "Jimari Botler", "Bot Gunnerson", "Nash Botmacher",
             "Botger Craig", "Dave RAMington", "MarLAN Lucky", "Rex Bothead", "Nbotukong Suh", "Grant Bostrom", "Ameer Botdullah", "Botinic Raiola", "Vince Ferraboto", "economybot",
             "NotaBot_Human", "psybot", "2020: the year of the bot")

    try:
        print("~~~ Attempting to change nickname...")
        await client.user.edit(username=random.choice(nicks))
        print(f"~~~ Changed nickname to {client.user.username}")

        if ctx:
            await ctx.send(f"Myw new name is... 🥁🥁🥁 {client.user.username}!")
    except discord.HTTPException as err:
        err_msg = "~~~ !!! " + str(err).replace("\n", " ")
        print(err_msg)
        if ctx:
            await ctx.send(err_msg)
    except:
        print(f"Unknown error!")


async def change_my_status(client, ctx=None):
    statuses = ("Husker Football 24/7", "Currently beating Florida 62-24", "Currently giving up 400 yards rushing to one guy", "Attempting a swing pass for -1 yards")
    try:
        print("~~~ Attempting to change status...")
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))
        print(f"~~~ Changed status to {client.user.username}")

        if ctx:
            await ctx.send(f"My new status is... 🥁🥁🥁 {client.user.username}!")
    except discord.HTTPException as err:
        err_msg = "~~~ !!! " + str(err).replace("\n", " ")
        print(err_msg)
        if ctx:
            await ctx.send(err_msg)
    except:
        print(f"Unknown error!")


def establish_logger(category: int):
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] [%(levelname)s]: %(message)s",
        datefmt="%d-%b-%y %H:%M:%S"
    )


def print_log(category: int, message: str):
    if category == logging.DEBUG:
        logging.debug(msg=message)
    elif category == logging.INFO:
        logging.info(msg=message)
    elif category == logging.WARNING:
        logging.warning(msg=message)
    elif category == logging.ERROR:
        logging.error(msg=message)
    elif category == logging.CRITICAL:
        logging.critical(msg=message)
