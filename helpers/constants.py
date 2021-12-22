# TODO
# * update and modernize
# TODO


import platform

import pytz
from dotenv import load_dotenv

from helpers.encryption import decrypt, decrypt_return_data, encrypt, load_key
from helpers.misc import loadVarPath


def log(level: int, message: str):
    import datetime

    if level == 0:
        print(f"[{datetime.datetime.now()}] ### Constants: {message}")
    elif level == 1:
        print(f"[{datetime.datetime.now()}] ### ~~~ Constants: {message}")


log(0, f"Platform == {platform.platform()}")

# Consistent timezone
TZ = pytz.timezone("CST6CDT")

# Setting variables location
variables_path = loadVarPath()
load_dotenv(dotenv_path=variables_path)

# Decrypt Env file
env_file = variables_path
key = load_key()

# Save decrypted file
run = False
if run:
    decrypt(env_file, key)
    encrypt(env_file, key)

env_vars = decrypt_return_data(env_file, key)

# SSH
SSH_HOST = env_vars["ssh_host"]
SSH_USERNAME = env_vars["ssh_username"]
SSH_PASSWORD = env_vars["ssh_password"]

# Imgur
IMGUR_CLIENT = env_vars["imgur_client"]
IMGUR_SECRET = env_vars["imgur_secret"]

# Discord Bot Tokens
TEST_TOKEN = env_vars["TEST_TOKEN"]
PROD_TOKEN = env_vars["DISCORD_TOKEN"]
BACKUP_TOKEN = env_vars["BACKUP_TOKEN"]

# SQL information
SQL_HOST = env_vars["sqlHost"]
SQL_USER = env_vars["sqlUser"]
SQL_PASSWD = env_vars["sqlPass"]
SQL_DB = env_vars["sqlDb"]

# Reddit Bot Info
REDDIT_CLIENT_ID = env_vars["reddit_client_id"]
REDDIT_SECRET = env_vars["reddit_secret"]
REDDIT_PW = env_vars["reddit_pw"]

# CFBD API Key
CFBD_KEY = env_vars["cfbd_api"]

# SSH Information
# SSH_HOST = env_vars["ssh_host"]
# SSH_USER = env_vars["ssh_user"]
# SSH_PW = env_vars["ssh_pw"]

# Twitter variables
TWITTER_KEY = env_vars["twitter_key"]
TWITTER_SECRET_KEY = env_vars["twitter_secret_key"]
TWITTER_BEARER = env_vars["twitter_bearer"]
TWITTER_TOKEN = env_vars["twitter_token"]
TWITTER_TOKEN_SECRET = env_vars["twitter_token_secret"]
TWITTER_HUSKER_MEDIA_LIST_ID = 1307680291285278720

# Weather API
WEATHER_API_KEY = env_vars["openweather_key"]

del env_vars, env_file, key

# Headers for `requests`
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
}

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

# Discord Channels
CHAN_ADMIN = 525519594417291284
CHAN_ADMIN_DOUBLE = 538419127535271946
CHAN_ANNOUNCEMENT = 651523695214329887
CHAN_BOTLOGS = 458474143403212801
CHAN_BOT_SPAM = 593984711706279937
CHAN_DISCUSSION_LIVE = 768828614773833768
CHAN_DISCUSSION_STREAMING = 768828705102888980
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

# Game Day Category
CAT_ADMIN = 600530901407105055
CAT_GAMEDAY = 768828439636606996
CAT_GENERAL = 440632687087058944
CAT_INTRO = 442062321695719434

CHAN_BANNED = (
    CHAN_ANNOUNCEMENT,
    CHAN_ANNOUNCEMENT,
    CHAN_BOTLOGS,
    CHAN_HOF,
    CHAN_HOS,
    CHAN_POLITICS,
)
CHAN_STATS_BANNED = (
    CHAN_ADMIN,
    CHAN_ADMIN_DOUBLE,
    CHAN_ANNOUNCEMENT,
    CHAN_BOTLOGS,
    CHAN_HOF,
    CHAN_HOS,
)
CHAN_HYPE_GROUP = (CHAN_HYPE_MAX, CHAN_HYPE_SOME, CHAN_HYPE_NO)

# Reactions
REACTION_HYPE_MAX = "📈"
REACTION_HYPE_SOME = "⚠"
REACTION_HYPE_NO = "⛔"

REACITON_HYPE_SQUAD = (REACTION_HYPE_MAX, REACTION_HYPE_SOME, REACTION_HYPE_NO)

# Servers/guilds
GUILD_PROD = 440632686185414677

# Member ID
MEMBER_BOT = 593949013443608596
MEMBER_GEE = 189554873778307073

# Currency
CURRENCY_NAME = "Husker Coins"

# Bot Info
BOT_DISPLAY_NAME = "Bot Frost"
BOT_GITHUB_URL = "https://github.com/refekt/Husker-Bot"
BOT_ICON_URL = "https://i.imgur.com/Ah3x5NA.png"
BOT_THUMBNAIL_URL = "https://ucomm.unl.edu/images/brand-book/Our-marks/nebraska-n.jpg"
BOT_FOOTER_SECRET = (
    "These messages are anonymous and there is no way to verify messages are accurate."
)
BOT_FOOTER_BOT = "Created by Bot Frost"

# DateTime format
DT_OBJ_FORMAT = "%d %b %Y %I:%M %p %Z"
DT_OBJ_FORMAT_TBA = "%d %b %Y"
DT_OPENWEATHER_UTC = "%H:%M:%S %Z"
DT_STR_FORMAT = "%b %d %Y %I:%M %p"
DT_STR_RECRUIT = "%m/%d/%Y %I:%M:%S %p"
DT_TASK_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DT_TBA_HR = 10
DT_TBA_MIN = 58
DT_TBA_TIME = "10:58 PM"
DT_TWEET_FORMAT = "%Y-%m-%d %H:%M:%S"

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
    {"State": "Puerto Rico", "Code": "PR"},
]
