import logging
import platform

import pytz
from cfbd import Configuration
from dotenv import load_dotenv

from helpers.encryption import decrypt, decrypt_return_data, encrypt, load_key
from helpers.misc import loadVarPath
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if "Windows" in platform.platform() else logging.INFO,
)

logger.info(f"Platform == {platform.platform()}")

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

# Discord Bot Tokens
PROD_TOKEN = env_vars["DISCORD_TOKEN"]
logger.info("Discord tokens loaded")

# SQL information
SQL_HOST = env_vars["sqlHost"]
SQL_USER = env_vars["sqlUser"]
SQL_PASSWD = env_vars["sqlPass"]
SQL_DB = env_vars["sqlDb"]
logger.info("MySQL variables loaded")

# TODO Reddit Bot Info...needed?
REDDIT_CLIENT_ID = env_vars["reddit_client_id"]
REDDIT_SECRET = env_vars["reddit_secret"]
REDDIT_PW = env_vars["reddit_pw"]

# DEBUG
DEBUGGING_CODE = "Windows" in platform.platform()

# Twitter variables
TWITTER_HUSKER_MEDIA_LIST_ID = 1307680291285278720
TWITTER_BLOCK16_SCREENANME = "Block16Omaha"
TWITTER_QUERY_MAX = 512
TWITTER_BEARER = env_vars["twitter_bearer"]
TWITTER_KEY = env_vars["twitter_api_key"]
TWITTER_SECRET_KEY = env_vars["twitter_api_key_secret"]
TWITTER_TOKEN = env_vars["twitter_access_token"]
TWITTER_TOKEN_SECRET = env_vars["twitter_access_token_secret"]
TWITTER_V2_CLIENT_ID = env_vars["twitter_v2_client_id"]
TWITTER_V2_CLIENT_SECRET = env_vars["twitter_v2_client_secret"]
TWITTER_TWEET_OBJECT: list[str] = [
    "data",
    "includes",
    "matching_rules",
]
TWITTER_EXPANSIONS: list[str] = [
    "attachments.media_keys",
    "attachments.poll_ids",
    "author_id",
    "entities.mentions.username",
    "geo.place_id",
    "in_reply_to_user_id",
    "referenced_tweets.id",
    "referenced_tweets.id.author_id",
]
TWITTER_MEDIA_FIELDS: list[str] = [
    # "alt_text",
    # "duration_ms",
    # "height",
    "media_key",
    "preview_image_url",
    # "public_metrics",
    "type",
    "url",
    # "width",
]
# TWITTER_PLACE_FIELDS: list[str] = [
#     "contained_within",
#     "country",
#     "country_code",
#     "full_name",
#     "geo",
#     "id",
#     "name",
#     "place_type",
# ]
# TWITTER_POLL_FIELDS: list[str] = [
#     "duration_minutes",
#     "end_datetime",
#     "id",
#     "options",
#     "voting_status",
# ]
TWITTER_TWEET_FIELDS: list[str] = [
    "attachments",
    "author_id",
    "context_annotations",
    "conversation_id",
    "created_at",
    "entities",
    # "geo",
    "id",
    "in_reply_to_user_id",
    # "lang",
    # "possibly_sensitive",
    "public_metrics",
    "referenced_tweets",
    "reply_settings",
    "source",
    "text",
    "withheld",
]
TWITTER_USER_FIELDS: list[str] = [
    "created_at",
    # "description",
    "entities",
    "id",
    # "location",
    "name",
    # "pinned_tweet_id",
    "profile_image_url",
    # "protected",
    "public_metrics",
    "url",
    "username",
    "verified",
    # "withheld",
]

logger.info("Twitter variables loaded")

# Weather API
WEATHER_API_KEY = env_vars["openweather_key"]
logger.info("Weather API key loaded")

# cfbd
CFBD_KEY = env_vars["cfbd_api"]

CFBD_CONFIG = Configuration()
CFBD_CONFIG.api_key["Authorization"] = CFBD_KEY
CFBD_CONFIG.api_key_prefix["Authorization"] = "Bearer"

del env_vars, env_file, key, variables_path
logger.info("Deleted environment variables, files, and key")

# Consistent timezone
TZ = pytz.timezone("CST6CDT")
logger.info(f"Timezone set as {TZ}")

# Headers for `requests`
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0"
}
logger.info("User-Agent Header loaded")

# TODO Discord Roles...needed?
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
CHAN_ADMIN: int = 525519594417291284
CHAN_ADMIN_DOUBLE: int = 538419127535271946
CHAN_ANNOUNCEMENT: int = 651523695214329887
CHAN_BOTLOGS: int = 458474143403212801
CHAN_BOT_SPAM: int = 593984711706279937
CHAN_BOT_SPAM_PRIVATE: int = 990262349703286864
CHAN_DISCUSSION_LIVE: int = 768828614773833768
CHAN_DISCUSSION_STREAMING: int = 768828705102888980
CHAN_FOOD: int = 453994941857923082
CHAN_GENERAL: int = 440868279150444544
CHAN_HOF: int = 487431877792104470
CHAN_HOS: int = 860686057850798090
CHAN_HYPE_MAX: int = 682386060264865953
CHAN_HYPE_NO: int = 682386220072042537
CHAN_HYPE_SOME: int = 682386133950136333
CHAN_IOWA: int = 749339421077274664
CHAN_NORTH_BOTTOMS: int = 620043869504929832
CHAN_POLITICS: int = 504777800100741120
CHAN_POSSUMS: int = 873645025878233099
CHAN_RECRUITING: int = 507520543096832001
CHAN_TWITTERVERSE: int = 636220560010903584
logger.info("Channel variables loaded")

# Game Day Category
CAT_GAMEDAY = 768828439636606996
CAT_GENERAL = 440632687087058944
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

CHAN_HYPE_GROUP = (CHAN_HYPE_MAX, CHAN_HYPE_SOME, CHAN_HYPE_NO)
logger.info("Hype channels loaded")

# Servers/guilds
GUILD_PROD = 440632686185414677
logger.info("Guild variable loaded")

# Member ID
MEMBER_GEE = 189554873778307073
logger.info("Member variables loaded")

# Bot Info
BOT_DISPLAY_NAME = "Bot Frost"
BOT_GITHUB_URL = "https://github.com/refekt/Husker-Bot"
BOT_ICON_URL = "https://i.imgur.com/Ah3x5NA.png"
BOT_THUMBNAIL_URL = "https://ucomm.unl.edu/images/brand-book/Our-marks/nebraska-n.jpg"
BOT_FOOTER_SECRET = (
    "These messages are anonymous and there is no way to verify messages are accurate."
)
BOT_FOOTER_BOT = "Bot Frost praises the sun \\[T]/"  # noqa
logger.info("Bot info variables loaded")

# DateTime format
DT_CFBD_GAMES = "%Y-%m-%dT%H:%M:%S.%f%z"
DT_CFBD_GAMES_DISPLAY = "%B %d, %Y at %H:%M %p %Z"
DT_FAP_RECRUIT = "%Y-%m-%d %H:%M:%S"
DT_GITHUB_API = "%Y-%m-%dT%H:%M:%SZ"
DT_GITHUB_API_DISPLAY = "%A, %B %d, %Y"
DT_MYSQL_FORMAT = "%Y-%m-%d %H:%M:%S"
DT_OBJ_FORMAT = "%d %b %Y %I:%M %p %Z"
DT_OPENWEATHER_UTC = "%H:%M:%S %Z"
DT_STR_FORMAT = "%b %d %Y %I:%M %p"
DT_STR_RECRUIT = "%m/%d/%Y %I:%M:%S %p"
DT_TASK_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DT_TBA_TIME = "10:58 PM"
DT_TWEET_FORMAT = "%H:%M:%S %d %b %Y"
logger.info("Datetime formatting variables loaded")

# Discord UI Timeout
GLOBAL_TIMEOUT = 3600

# Croot bot
CROOT_SEARCH_LIMIT = 5

# Embed limitations
# https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
DESC_LIMIT = 4096
EMBED_MAX = 6000
FIELDS_LIMIT = 25
FIELD_VALUE_LIMIT = 1024
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

# Schedule Posts
SCHED_DAY_IMG: str = "https://i.imgur.com/8KPOgoq.png"
SCHED_NIGHT_IMG: str = "https://i.imgur.com/4c3lZQj.jpg"

logger.info("Discord Union group variables loaded")

__all__: list[str] = [
    "BOT_DISPLAY_NAME",
    "BOT_FOOTER_BOT",
    "BOT_FOOTER_SECRET",
    "BOT_GITHUB_URL",
    "BOT_ICON_URL",
    "BOT_THUMBNAIL_URL",
    "CAT_GAMEDAY",
    "CAT_GENERAL",
    "CFBD_CONFIG",
    "CFBD_KEY",
    "CHAN_ADMIN",
    "CHAN_ADMIN_DOUBLE",
    "CHAN_ANNOUNCEMENT",
    "CHAN_BANNED",
    "CHAN_BOTLOGS",
    "CHAN_BOT_SPAM",
    "CHAN_BOT_SPAM_PRIVATE",
    "CHAN_DISCUSSION_LIVE",
    "CHAN_DISCUSSION_STREAMING",
    "CHAN_FOOD",
    "CHAN_GENERAL",
    "CHAN_HOF",
    "CHAN_HOS",
    "CHAN_HYPE_GROUP",
    "CHAN_HYPE_MAX",
    "CHAN_HYPE_NO",
    "CHAN_HYPE_SOME",
    "CHAN_IOWA",
    "CHAN_POLITICS",
    "CHAN_POSSUMS",
    "CHAN_RECRUITING",
    "CHAN_TWITTERVERSE",
    "CROOT_SEARCH_LIMIT",
    "DEBUGGING_CODE",
    "DESC_LIMIT",
    "DT_CFBD_GAMES",
    "DT_CFBD_GAMES_DISPLAY",
    "DT_FAP_RECRUIT",
    "DT_GITHUB_API",
    "DT_GITHUB_API_DISPLAY",
    "DT_MYSQL_FORMAT",
    "DT_OBJ_FORMAT",
    "DT_OPENWEATHER_UTC",
    "DT_STR_FORMAT",
    "DT_STR_RECRUIT",
    "DT_TASK_FORMAT",
    "DT_TBA_TIME",
    "DT_TWEET_FORMAT",
    "EMBED_MAX",
    "FIELDS_LIMIT",
    "FIELD_NAME_LIMIT",
    "FIELD_VALUE_LIMIT",
    "FOOTER_LIMIT",
    "GLOBAL_TIMEOUT",
    "GUILD_PROD",
    "HEADERS",
    "MEMBER_GEE",
    "NAME_LIMIT",
    "PROD_TOKEN",
    "RECRUIT_POSITIONS",
    "RECRUIT_STATES",
    "REDDIT_CLIENT_ID",
    "REDDIT_PW",
    "REDDIT_SECRET",
    "ROLE_ADMIN_PROD",
    "ROLE_ADMIN_TEST",
    "ROLE_AIRPOD",
    "ROLE_ALDIS",
    "ROLE_ASPARAGUS",
    "ROLE_EVERYONE_PROD",
    "ROLE_GUMBY",
    "ROLE_HYPE_MAX",
    "ROLE_HYPE_NO",
    "ROLE_HYPE_SOME",
    "ROLE_ISMS",
    "ROLE_LILRED",
    "ROLE_MEME",
    "ROLE_MINECRAFT",
    "ROLE_MOD_PROD",
    "ROLE_PACKER",
    "ROLE_PIXEL",
    "ROLE_POTATO",
    "ROLE_QDOBA",
    "ROLE_RUNZA",
    "ROLE_TARMAC",
    "ROLE_TIME_OUT",
    "SCHED_DAY_IMG",
    "SCHED_NIGHT_IMG",
    "SQL_DB",
    "SQL_HOST",
    "SQL_PASSWD",
    "SQL_USER",
    "TITLE_LIMIT",
    "TWITTER_BEARER",
    "TWITTER_BLOCK16_SCREENANME",
    "TWITTER_HUSKER_MEDIA_LIST_ID",
    "TWITTER_KEY",
    "TWITTER_MEDIA_FIELDS",
    "TWITTER_QUERY_MAX",
    "TWITTER_SECRET_KEY",
    "TWITTER_TOKEN",
    "TWITTER_TOKEN_SECRET",
    "TWITTER_TWEET_FIELDS",
    "TWITTER_TWEET_OBJECT",
    "TWITTER_USER_FIELDS",
    "TWITTER_V2_CLIENT_ID",
    "TWITTER_V2_CLIENT_SECRET",
    "TZ",
    "US_STATES",
    "WEATHER_API_KEY",
    "TWITTER_EXPANSIONS",
    # "TWITTER_PLACE_FIELDS",
    # "TWITTER_POLL_FIELDS",
]

logger.info(f"{str(__name__).title()} module loaded!")
