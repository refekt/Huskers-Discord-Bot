import logging
import platform
from typing import Union

import discord
import pytz
from cfbd import Configuration
from discord import (
    CategoryChannel,
    ForumChannel,
    PartialMessageable,
    StageChannel,
    TextChannel,
    Thread,
    VoiceChannel,
)
from dotenv import load_dotenv

from helpers.encryption import decrypt, decrypt_return_data, encrypt, load_key
from helpers.misc import loadVarPath

logger = logging.getLogger(__name__)

logger.info(f"Platform == {platform.platform()}")

# Consistent timezone
TZ = pytz.timezone("CST6CDT")
logger.info(f"Timezone set as {TZ}")

# Setting variables location
variables_path = loadVarPath()
load_dotenv(dotenv_path=variables_path)
logger.info("Environment path loaded")

# Decrypt Env file
env_file = variables_path
key = load_key()
logger.info("Encryption key loaded")

# DEBUGGING Save decrypted file
run = False
if run:
    decrypt(env_file, key)
    encrypt(env_file, key)

env_vars = decrypt_return_data(env_file, key)
logger.info("Environment variables loaded")

# SSH
SSH_HOST = env_vars["ssh_host"]
SSH_USERNAME = env_vars["ssh_username"]
SSH_PASSWORD = env_vars["ssh_password"]
logger.info("SSH variables loaded")

# Imgur
IMGUR_CLIENT = env_vars["imgur_client"]
IMGUR_SECRET = env_vars["imgur_secret"]
logger.info("Imgur variables loaded")

# Discord Bot Tokens
TEST_TOKEN = env_vars["TEST_TOKEN"]
PROD_TOKEN = env_vars["DISCORD_TOKEN"]
BACKUP_TOKEN = env_vars["BACKUP_TOKEN"]
logger.info("Discord tokens loaded")

# SQL information
SQL_HOST = env_vars["sqlHost"]
SQL_USER = env_vars["sqlUser"]
SQL_PASSWD = env_vars["sqlPass"]
SQL_DB = env_vars["sqlDb"]
logger.info("MySQL variables loaded")

# Reddit Bot Info
REDDIT_CLIENT_ID = env_vars["reddit_client_id"]
REDDIT_SECRET = env_vars["reddit_secret"]
REDDIT_PW = env_vars["reddit_pw"]

# CFBD API Key
CFBD_KEY = env_vars["cfbd_api"]
logger.info("CFBD key loaded")

# DEBUG
DEBUGGING_CODE = "Windows" in platform.platform()

# Twitter variables
TWITTER_HUSKER_MEDIA_LIST_ID = 1307680291285278720
TWITTER_BLOCK16_ID_STR = "457066083"
TWITTER_BLOCK16_SCREENANME = "Block16Omaha"
TWITTER_QUERY_MAX = 512

TWITTER_BEARER = env_vars["twitter_bearer"]

TWITTER_KEY = env_vars["twitter_api_key"]
TWITTER_SECRET_KEY = env_vars["twitter_api_key_secret"]

TWITTER_TOKEN = env_vars["twitter_access_token"]
TWITTER_TOKEN_SECRET = env_vars["twitter_access_token_secret"]

TWITTER_V2_CLIENT_ID = env_vars["twitter_v2_client_id"]
TWITTER_V2_CLIENT_SECRET = env_vars["twitter_v2_client_secret"]

logger.info("Twitter variables loaded")

# Weather API
WEATHER_API_KEY = env_vars["openweather_key"]
logger.info("Weather API key loaded")

# cfbd
CFBD_CONFIG = Configuration()
CFBD_CONFIG.api_key["Authorization"] = CFBD_KEY
CFBD_CONFIG.api_key_prefix["Authorization"] = "Bearer"

del env_vars, env_file, key
logger.info("Deleted environment variables, files, and key")

# Headers for `requests`
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
}
logger.info("User-Agent Header loaded")

# Discord Roles
ROLE_ADMIN_PROD = 440639061191950336
ROLE_ADMIN_TEST = 606301197426753536
ROLE_AIRPOD = 633702209703378978
ROLE_ALDIS = 802639913824550952
ROLE_ASPARAGUS = 583842403341828115
ROLE_EVERYONE_PROD = 440632686185414677
ROLE_GUMBY = 459569717430976513
ROLE_HYPE_MAX = 682380058261979176
ROLE_HYPE_NO = 682380119666720789
ROLE_HYPE_SOME = 682380101077434480
ROLE_ISMS = 592425861534449674
ROLE_LILRED = 464903715854483487
ROLE_MEME = 448690298760200195
ROLE_MINECRAFT = 661409899481268238
ROLE_MOD_PROD = 443805741111836693
ROLE_PACKER = 609409451836964878
ROLE_PIXEL = 633698252809699369
ROLE_POTATO = 583842320575889423
ROLE_QDOBA = 797587264112820264
ROLE_RUNZA = 485086088017215500
ROLE_TARMAC = 881546056687583242
ROLE_TIME_OUT = 663881203983843338
logger.info("Role variables loaded")

# Discord Channels
CHAN_ADMIN = 525519594417291284
CHAN_ADMIN_DOUBLE = 538419127535271946
CHAN_ANNOUNCEMENT = 651523695214329887
CHAN_BOTLOGS = 458474143403212801
CHAN_BOT_SPAM = 593984711706279937
CHAN_DISCUSSION_LIVE = 768828614773833768
CHAN_DISCUSSION_STREAMING = 768828705102888980
CHAN_FOOD = 453994941857923082
CHAN_GENERAL = 440868279150444544
CHAN_HOF = 487431877792104470
CHAN_HOS = 860686057850798090
CHAN_HYPE_MAX = 682386060264865953
CHAN_HYPE_NO = 682386220072042537
CHAN_HYPE_SOME = 682386133950136333
CHAN_IOWA = 749339421077274664
CHAN_NOBOS = 620043869504929832
CHAN_POLITICS = 504777800100741120
CHAN_POSSUMS = 873645025878233099
CHAN_RECRUITING = 507520543096832001
CHAN_TWITTERVERSE = 636220560010903584
logger.info("Channel variables loaded")

# Game Day Category
CAT_ADMIN = 600530901407105055
CAT_GAMEDAY = 768828439636606996
CAT_GENERAL = 440632687087058944
CAT_INTRO = 442062321695719434
logger.info("Channel category variables loaded")

CHAN_BANNED = (
    CHAN_ANNOUNCEMENT,
    CHAN_ANNOUNCEMENT,
    CHAN_BOTLOGS,
    CHAN_HOF,
    CHAN_HOS,
    CHAN_POLITICS,
)
logger.info("Banned channels loaded")

CHAN_STATS_BANNED = (
    CHAN_ADMIN,
    CHAN_ADMIN_DOUBLE,
    CHAN_ANNOUNCEMENT,
    CHAN_BOTLOGS,
    CHAN_HOF,
    CHAN_HOS,
)
logger.info("Banned channel stats loaded")

CHAN_HYPE_GROUP = (CHAN_HYPE_MAX, CHAN_HYPE_SOME, CHAN_HYPE_NO)
logger.info("Hype channels loaded")

# Servers/guilds
GUILD_PROD = 440632686185414677
GUILD_TEST = 595705205069185045
logger.info("Guild variable loaded")

# Member ID
MEMBER_BOT = 593949013443608596
MEMBER_GEE = 189554873778307073
logger.info("Member variables loaded")

# Currency
CURRENCY_NAME = "Husker Coins"
logger.info("Currency variable loaded")

# Bot Info
BOT_DISPLAY_NAME = "Bot Frost"
BOT_GITHUB_URL = "https://github.com/refekt/Husker-Bot"
BOT_ICON_URL = "https://i.imgur.com/Ah3x5NA.png"
BOT_THUMBNAIL_URL = "https://ucomm.unl.edu/images/brand-book/Our-marks/nebraska-n.jpg"
BOT_FOOTER_SECRET = (
    "These messages are anonymous and there is no way to verify messages are accurate."
)
BOT_FOOTER_BOT = "Created by Bot Frost"
logger.info("Bot info variables loaded")

# DateTime format
DT_CFBD_GAMES = "%Y-%m-%dT%H:%M:%S.%f%z"
DT_CFBD_GAMES_DISPLAY = "%H:%M %p %Z %B %d, %Y"
DT_FAP_RECRUIT = "%Y-%m-%d %H:%M:%S"
DT_MYSQL_FORMAT = "%Y-%m-%d %H:%M:%S"
DT_OBJ_FORMAT = "%d %b %Y %I:%M %p %Z"
DT_OBJ_FORMAT_TBA = "%d %b %Y"
DT_OPENWEATHER_UTC = "%H:%M:%S %Z"
DT_STR_FORMAT = "%b %d %Y %I:%M %p"
DT_STR_RECRUIT = "%m/%d/%Y %I:%M:%S %p"
DT_TASK_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DT_TBA_HR = 10
DT_TBA_MIN = 58
DT_TBA_TIME = "10:58 PM"
DT_TWEET_FORMAT = "%H:%M:%S %d %b %Y"
DT_TWEET_FORMAT_OLD = "%Y-%m-%d %H:%M:%S"
logger.info("Datetime formatting variables loaded")

GLOBAL_TIMEOUT = 3600

CROOT_SEARCH_LIMIT = 5

# Embed limitations
# https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
DESC_LIMIT = 4096
EMBED_MAX = 6000
FIELD_VALUE_LIMIT = 1024
FIELDS_LIMIT = 25
FOOTER_LIMIT = 2048
TITLE_LIMIT = NAME_LIMIT = FIELD_NAME_LIMIT = 256

# States
US_STATES = [
    {"State": "Alabama", "Abbrev": "Ala.", "Code": "AL"},
    {"State": "Alaska", "Abbrev": "Alaska", "Code": "AK"},
    {"State": "Arizona", "Abbrev": "Ariz.", "Code": "AZ"},
    {"State": "Arkansas", "Abbrev": "Ark.", "Code": "AR"},
    {"State": "California", "Abbrev": "Calif.", "Code": "CA"},
    {"State": "Colorado", "Abbrev": "Colo.", "Code": "CO"},
    {"State": "Connecticut", "Abbrev": "Conn.", "Code": "CT"},
    {"State": "Delaware", "Abbrev": "Del.", "Code": "DE"},
    {"State": "District of Columbia", "Abbrev": "D.C.", "Code": "DC"},
    {"State": "Florida", "Abbrev": "Fla.", "Code": "FL"},
    {"State": "Georgia", "Abbrev": "Ga.", "Code": "GA"},
    {"State": "Hawaii", "Abbrev": "Hawaii", "Code": "HI"},
    {"State": "Idaho", "Abbrev": "Idaho", "Code": "ID"},
    {"State": "Illinois", "Abbrev": "Ill.", "Code": "IL"},
    {"State": "Indiana", "Abbrev": "Ind.", "Code": "IN"},
    {"State": "Iowa", "Abbrev": "Iowa", "Code": "IA"},
    {"State": "Kansas", "Abbrev": "Kans.", "Code": "KS"},
    {"State": "Kentucky", "Abbrev": "Ky.", "Code": "KY"},
    {"State": "Louisiana", "Abbrev": "La.", "Code": "LA"},
    {"State": "Maine", "Abbrev": "Maine", "Code": "ME"},
    {"State": "Maryland", "Abbrev": "Md.", "Code": "MD"},
    {"State": "Massachusetts", "Abbrev": "Mass.", "Code": "MA"},
    {"State": "Michigan", "Abbrev": "Mich.", "Code": "MI"},
    {"State": "Minnesota", "Abbrev": "Minn.", "Code": "MN"},
    {"State": "Mississippi", "Abbrev": "Miss.", "Code": "MS"},
    {"State": "Missouri", "Abbrev": "Mo.", "Code": "MO"},
    {"State": "Montana", "Abbrev": "Mont.", "Code": "MT"},
    {"State": "Nebraska", "Abbrev": "Nebr.", "Code": "NE"},
    {"State": "Nevada", "Abbrev": "Nev.", "Code": "NV"},
    {"State": "New Hampshire", "Abbrev": "N.H.", "Code": "NH"},
    {"State": "New Jersey", "Abbrev": "N.J.", "Code": "NJ"},
    {"State": "New Mexico", "Abbrev": "N.M.", "Code": "NM"},
    {"State": "New York", "Abbrev": "N.Y.", "Code": "NY"},
    {"State": "North Carolina", "Abbrev": "N.C.", "Code": "NC"},
    {"State": "North Dakota", "Abbrev": "N.D.", "Code": "ND"},
    {"State": "Ohio", "Abbrev": "Ohio", "Code": "OH"},
    {"State": "Oklahoma", "Abbrev": "Okla.", "Code": "OK"},
    {"State": "Oregon", "Abbrev": "Ore.", "Code": "OR"},
    {"State": "Pennsylvania", "Abbrev": "Pa.", "Code": "PA"},
    {"State": "Rhode Island", "Abbrev": "R.I.", "Code": "RI"},
    {"State": "South Carolina", "Abbrev": "S.C.", "Code": "SC"},
    {"State": "South Dakota", "Abbrev": "S.D.", "Code": "SD"},
    {"State": "Tennessee", "Abbrev": "Tenn.", "Code": "TN"},
    {"State": "Texas", "Abbrev": "Tex.", "Code": "TX"},
    {"State": "Utah", "Abbrev": "Utah", "Code": "UT"},
    {"State": "Vermont", "Abbrev": "Vt.", "Code": "VT"},
    {"State": "Virginia", "Abbrev": "Va.", "Code": "VA"},
    {"State": "Washington", "Abbrev": "Wash.", "Code": "WA"},
    {"State": "West Virginia", "Abbrev": "W.Va.", "Code": "WV"},
    {"State": "Wisconsin", "Abbrev": "Wis.", "Code": "WI"},
    {"State": "Wyoming", "Abbrev": "Wyo.", "Code": "WY"},
    {"State": "Puerto Rico", "Abbrev": "PR", "Code": "PR"},
]

RECRUIT_STATES = {
    "Alabama": "AL",
    "Alaska": "AK",
    "American Samoa": "AS",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "British Columbia": "BC",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District Of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

RECRUIT_POSITIONS = {
    "APB": "All-Purpose Back",
    "ATH": "Athlete",
    "CB": "Cornerback",
    "DL": "Defensive Lineman",
    "DT": "Defensive Tackle",
    "DUAL": "Dual-Threat Quarterback",
    "Edge": "Edge",
    "FB": "Fullback",
    "ILB": "Inside Linebacker",
    "IOL": "Interior Offensive Lineman",
    "K": "Kicker",
    "LB": "Linebacker",
    "LS": "Long Snapper",
    "OC": "Center",
    "OG": "Offensive Guard",
    "OLB": "Outside Linebacker",
    "OT": "Offensive Tackle",
    "P": "Punter",
    "PRO": "Pro-Style Quarterback",
    "QB": "Quarterback",
    "RB": "Running Back",
    "RET": "Returner",
    "S": "Safety",
    "SDE": "Strong-Side Defensive End",
    "TE": "Tight End",
    "WDE": "Weak-Side Defensive End",
    "WR": "Wide Receiver",
}

DISCORD_CHANNEL_TYPES = Union[
    VoiceChannel,
    StageChannel,
    TextChannel,
    ForumChannel,
    CategoryChannel,
    Thread,
    PartialMessageable,
    None,
]
DISCORD_USER_TYPES = Union[discord.Member, discord.User]

logger.info("Discord Union group variables loaded")

__all__ = [
    item
    for item in globals()
    if not item[1].islower() and (not item.startswith("__") or not item.startswith("_"))
]  # Get rid of all local variables and imports.

logger.info(f"{str(__name__).title()} module loaded!")
