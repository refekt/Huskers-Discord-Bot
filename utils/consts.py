import os
import platform
import sys

import pytz
from dotenv import load_dotenv

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
        load_dotenv(dotenv_path="/home/botfrost_test/variables.env")
else:
    print(f"Unknown Platform: {platform.platform()}")

# Cooldown rates for commands
_global_rate = os.getenv("global_rate")
_global_per = os.getenv("global_per")

# Custom variables hosted in `variables.env` to prevent showing on Git
host = os.getenv("sqlHost")
user = os.getenv("sqlUser")
passwd = os.getenv("sqlPass")
db = os.getenv("sqlDb")
test_token = os.getenv("TEST_TOKEN")
prod_token = os.getenv("DISCORD_TOKEN")
reddit_client_id = os.getenv("reddit_client_id")
reddit_secret = os.getenv("reddit_secret")
reddit_pw = os.getenv("reddit_pw")
ssh_host = os.getenv("ssh_host")
ssh_user = os.getenv("ssh_user")
ssh_pw = os.getenv("ssh_pw")

# Headers for `requests`
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'}

# Consistent timezone
tz = pytz.timezone("US/Central")


# Discord Roles
role_admin_prod = 440639061191950336
role_admin_test = 606301197426753536
role_mod_prod = 443805741111836693
role_potato = 583842320575889423
role_asparagus = 583842403341828115
role_lilred = 464903715854483487
role_runza = 485086088017215500
role_meme = 448690298760200195
role_isms = 592425861534449674
role_packer = 609409451836964878
role_pixel = 633698252809699369
role_airpod = 633702209703378978
role_gumby = 459569717430976513
role_minecraft = 661409899481268238

# Discord Channels
chan_HOF_prod = 487431877792104470
chan_HOF_test = 616824929383612427
chan_dbl_war_room = 538419127535271946
chan_war_room = 525519594417291284
chan_botlogs = 458474143403212801
chan_scott = 507520543096832001
chan_rules = 651523695214329887

# bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]
