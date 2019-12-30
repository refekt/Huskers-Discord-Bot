import datetime
import json
import os
import platform
import re
import sys

import pytz
import requests
from bitlyshortener import Shortener
from bs4 import BeautifulSoup
from bs4 import element
from discord.ext import commands
from dotenv import load_dotenv

from utils.mysql import process_MySQL, sqlTeamIDs as TeamIDs

# from google import search

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

_global_rate = os.getenv("global_rate")
_global_per = os.getenv("global_per")

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

# Testing getenv()
# print(
# _global_rate, "\n",
# _global_per, "\n",
# host, "\n",
# user, "\n",
# passwd, "\n",
# db, "\n",
# test_token, "\n",
# prod_token, "\n",
# reddit_secret, "\n",
# reddit_client_id, "\n",
# reddit_pw, "\n",
# ssh_pw, "\n",
# ssh_user, "\n",
# ssh_host
# )

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'}

tz = pytz.timezone("US/Central")

states = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
          'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
          'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
          'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
          'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
          'District Of Columbia': "DC"}

SeasonWeeks = {
    0: datetime.datetime(year=2019, month=8, day=24, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    1: datetime.datetime(year=2019, month=8, day=31, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    2: datetime.datetime(year=2019, month=9, day=7, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    3: datetime.datetime(year=2019, month=9, day=14, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    4: datetime.datetime(year=2019, month=9, day=21, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    5: datetime.datetime(year=2019, month=9, day=28, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    6: datetime.datetime(year=2019, month=10, day=5, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    7: datetime.datetime(year=2019, month=10, day=12, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    8: datetime.datetime(year=2019, month=10, day=19, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    9: datetime.datetime(year=2019, month=10, day=26, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    10: datetime.datetime(year=2019, month=11, day=2, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    11: datetime.datetime(year=2019, month=11, day=9, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    12: datetime.datetime(year=2019, month=11, day=16, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    13: datetime.datetime(year=2019, month=11, day=23, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    14: datetime.datetime(year=2019, month=11, day=20, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    15: datetime.datetime(year=2019, month=12, day=7, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz),
    16: datetime.datetime(year=2019, month=12, day=14, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
}

admin_prod = 440639061191950336
mod_prod = 443805741111836693
admin_test = 606301197426753536
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

chan_HOF_prod = 487431877792104470
chan_HOF_test = 616824929383612427
chan_dbl_war_room = 538419127535271946
chan_war_room = 525519594417291284
chan_botlogs = 458474143403212801
chan_scott = 507520543096832001
chan_rules = 651523695214329887


bet_emojis = ["⬆", "⬇", "❎", "⏫", "⏬", "❌", "🔼", "🔽", "✖"]

# def CurrentWeek():
#     now = datetime.datetime(year=datetime.datetime.utcnow().year, month=datetime.datetime.utcnow().month, day=datetime.datetime.utcnow().day, hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
#     index = len(SeasonWeeks) - 1
#     while index > -1:
#         if SeasonWeeks[index] <= now:
#             return index
#         index -= 1


class HuskerDotComSchedule():
    opponent = None
    game_date_time = None
    tv_station = None
    radio_station = None
    conference_game = False
    ranking = None
    outcome = None
    boxscore_url = None
    recap_url = None
    notes_url = None
    quotes_url = None
    history_url = None
    gallery_url = None
    location = None

    def __init__(self, opponent, game_date_time, tv_station, radio_station, conference_game, ranking, outcome, boxscore_url, recap_url, notes_url, quotes_url, history_url, gallery_url, location):
        self.opponent = opponent
        self.game_date_time = game_date_time
        self.tv_station = tv_station
        self.radio_station = radio_station
        self.conference_game = conference_game
        self.ranking = ranking
        self.outcome = outcome
        self.boxscore_url = boxscore_url
        self.recap_url = recap_url
        self.notes_url = notes_url
        self.quotes_url = quotes_url
        self.history_url = history_url
        self.gallery_url = gallery_url
        self.location = location


def ScheduleBackup(year=datetime.datetime.now().year, shorten=False):
    r = requests.get(url=f"https://huskers.com/sports/football/schedule/{year}", headers=headers)

    if not r.status_code == 200:
        return

    soup = BeautifulSoup(r.content, "html.parser")

    games_raw = soup.find_all("div", class_="sidearm-schedule-game-row flex flex-wrap flex-align-center row")
    games = []

    g = ""

    bitly_oauth_token = [os.getenv("bitly_oauth")]
    shortener = Shortener(tokens=bitly_oauth_token, max_cache_size=128)

    def shorten_url(url):
        return shortener.shorten_urls(long_urls=[url])[0]

    for index, game in enumerate(games_raw):
        o = ""
        ranking = ""

        if index > 0:  # Games after the first week of the season
            g = game.contents[1].contents[3].contents[1].text  # Current season? 2019?

            if g == "":  # Seasons prior or after?
                g = game.contents[1].contents[3].contents[3].contents[3].conents[1].text

            o = game.contents[1].contents[3].contents[3].contents[3].contents[0]

            if o == "\n":  # After the first week?
                o = game.contents[1].contents[3].contents[3].contents[3].contents[1].contents[0]

            if "#" in o:  # Ranked opponents?
                ranking = o
                o = game.contents[1].contents[3].contents[3].contents[3].contents[3].contents[0]

        elif index == 0:  # First game of the season. Usually the Spring game
            g = game.contents[1].contents[1].contents[1].text  # Current season? 2019?

            if g == "":  # Seasons prior or after
                g = game.contents[1].contents[3].contents[1].contents[1].text

            try:  # Current season? 2019?
                o = game.contents[1].contents[1].contents[3].contents[3].contents[0]
            except IndexError:  # Seasons prior or after
                o = game.contents[1].contents[3].contents[3].contents[3].contents[1].contents[0]

        outcome = str(game.contents[5].contents[1].text).replace("\n", "").replace(",", ", ")
        outcome_found = ("L," in outcome) or ("W," in outcome)
        if not outcome_found:
            outcome = None

        o = str(o).replace("\r", "").replace("\n", "").lstrip().rstrip()
        g = g.split("\n")

        tv_stations = ["ESPN", "FOX", "FS1", "ABC", "BTN"]
        months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        big_ten_members = ["Indiana", "Maryland", "Michigan", "Michigan State", "Ohio State", "Peen State", "Rutgers", "Illinois", "Iowa", "Minnesota", "Nebraska", "Northwestern", "Purdue",
                           "Wisconsin"]
        raw_date = raw_time = _tv_station = _radio_station = _conference_game = ""

        for team in big_ten_members:
            if team == o:
                _conference_game = True

        for ele in g:
            if ele[0:3].upper() in months:
                raw_date = ele.split(" (")[0] + ' ' + str(year)

            if ("PM" in ele) or ("AM" in ele) or ("A.M." in ele.upper()) or ("P.M." in ele.upper()):
                raw_time = ele.rstrip()
                if "." in raw_time:
                    raw_time = raw_time.replace(".", "").upper()
                    raw_time = raw_time[0:2] + ":00 " + raw_time[-2:]

            if ele == "TBA ":
                raw_time = "11:00 PM"

            if ele in tv_stations:
                _tv_station = ele.rstrip()

            if ele == "Husker Sports Network":
                _radio_station = "Huskers Sports Network"

        _game_date_time = datetime.datetime.strptime(f"{raw_date} {raw_time}", "%b %d %Y %I:%M %p").astimezone(tz=tz)

        _game_links_raw = game.contents[5].contents[3].contents[1].contents

        _game_boxscore_url = _game_recap_url = _game_notes_url = _game_quotes_url = _game_gallery_url = _game_history_url = ""

        husker_url = "https://huskers.com"

        for ele in _game_links_raw:
            if not ele == '\n':
                if ele.text == 'History':
                    _game_history_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']
                elif ele.text == 'Box Score':
                    _game_boxscore_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']
                elif ele.text == 'Recap':
                    _game_recap_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']
                elif ele.text == 'Notes':
                    _game_notes_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']
                elif ele.text == 'Quotes':
                    _game_quotes_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']
                elif ele.text == 'Gallery':
                    _game_gallery_url = shorten_url(husker_url + ele.contents[0].attrs['href']) if shorten else husker_url + ele.contents[0].attrs['href']

        # Credit to: https://stackoverflow.com/questions/22726860/beautifulsoup-webscraping-find-all-finding-exact-match
        loc = soup.find_all(lambda tag: tag.name == "div" and tag.get("class") == ["sidearm-schedule-game-location"])
        states_old = {"Ala.": "AL", "Alaska": "AK", "Ariz.": "AZ", "Ark.": "AR", "Calif.": "CA", "Colo.": "CO", "Conn.": "CT", "Del.": "DE", "D.C.": "DC", "Fla.": "FL", "Ga.": "GA", "Hawaii": "HI",
                  "Idaho": "ID", "Ill.": "IL", "Ind.": "IN", "Iowa": "IA", "Kan.": "KS", "Ky.": "KY", "La.": "LA", "Maine": "ME", "Md.": "MD", "Mass.": "MA", "Mich.": "MI", "Minn.": "MN",
                  "Miss.": "MS", "Mo.": "MO", "Mont.": "MT", "Neb.": "NE", "Nev.": "NV", "N.H.": "NH", "N.J.": "NJ", "N.M.": "NM", "N.Y.": "NY", "N.C.": "NC", "N.D.": "ND", "Ohio": "OH",
                  "Okla.": "OK", "Ore.": "OR", "Pa.": "PA", "R.I.": "RI", "S.C.": "SC", "S.D.": "SD", "Tenn.": "TN", "Texas": "TX", "Utah": "UT", "Vt.": "VT", "Va.": "VA", "Wash.": "WA",
                  "W.Va.": "WV", "Wis.": "WI", "Wyo.": "WY"}

        def game_location(index):
            if loc[index].text.strip() == "Memorial Stadium":
                return ["Lincoln", "NE"]
            else:
                city_state = loc[index].text.strip().split(", ")

                city = city_state[0]
                state = states_old[city_state[1]]
                return [city, state]

        games.append(
            HuskerDotComSchedule(
                opponent=o,
                game_date_time=_game_date_time,
                tv_station=_tv_station,
                radio_station=_radio_station,
                conference_game=_conference_game,
                ranking=ranking,
                outcome=outcome,
                boxscore_url=_game_boxscore_url,
                recap_url=_game_recap_url,
                notes_url=_game_notes_url,
                quotes_url=_game_quotes_url,
                history_url=_game_history_url,
                gallery_url=_game_gallery_url,
                location=game_location(index)
            )
        )

    return games


def Venue():
    r = requests.get("https://api.collegefootballdata.com/venues")
    return r.json()


def position_abbr(position):
    long_positions = {'PRO': 'Pro-Style Quarterback', 'DUAL': 'Dual-Threat Quarterback', 'APB': 'All-Purpose Back', 'RB': 'Running Back', 'FB': 'Fullback', 'WR': 'Wide Receiver', 'TE': 'Tight End',
                      'OT': 'Offensive Tackle', 'OG': 'Offensive Guard', 'OC': 'Center', 'SDE': 'Strong-Side Defensive End', 'WDE': 'Weak-Side Defensive End', 'DT': 'Defensive Tackle',
                      'ILB': 'Inside Linebacker', 'OLB': 'Outside Linebacker', 'CB': 'Cornerback', 'S': 'Safety', 'ATH': 'Athlete', 'K': 'Kicker', 'P': 'Punter', 'LS': 'Long Snapper',
                      'RET': 'Returner'}
    return long_positions[position]


class RecruitInterest():
    school = None
    offered = None
    status = None

    def __init__(self, school, offered, status=None):
        self.school = school
        self.offered = offered
        self.status = status


class Recruit():
    x247_highlights = None
    x247_profile = None
    all_time_ranking = None
    bio = None
    city = None
    commitment_date = None
    committed = None
    committed_school = None
    early_enrollee = None
    early_signee = None
    height = None
    key = None
    name = None
    national_ranking = None
    position = None
    position_ranking = None
    predictions = None
    rating_numerical = None
    rating_stars = None
    recruit_interests = None
    recruit_interests_url = None
    red_shirt = None
    rivals_ID = None
    rivals_profile = None
    rivals_highlights = None
    school = None
    school_type = None
    scout_evaluation = None
    state = None
    state_abbr = None
    state_ranking = None
    thumbnail = None
    twitter = None
    walk_on = None
    weight = None
    year = None

    def __init__(self=None, x247_highlights=None, x247_profile=None, all_time_ranking=None, bio=None, city=None, commitment_date=None, committed=None, committed_school=None, early_enrollee=None,
                 early_signee=None, height=None, key=None, name=None, national_ranking=None, position=None, position_ranking=None, predictions=None, rating_numerical=None,
                 rating_stars=None, recruit_interests=None, recruit_interests_url=None, red_shirt=None, rivals_ID=None, rivals_profile=None, rivals_highlights=None, school=None, school_type=None,
                 scout_evaluation=None, state=None, state_abbr=None, state_ranking=None, thumbnail=None, twitter=None, walk_on=None, weight=None, year=None):
        self.x247_highlights = x247_highlights
        self.x247_profile = x247_profile
        self.all_time_ranking = all_time_ranking
        self.bio = bio
        self.city = city
        try:
            self.commitment_date = datetime.datetime.strptime(commitment_date, "%m/%d/%Y %I:%M:%S %p")
        except:
            self.commitment_date = commitment_date
        self.committed = committed
        self.committed_school = committed_school
        self.early_enrollee = early_enrollee
        self.early_signee = early_signee
        self.height = str(height).replace("-", "' ") + "\""
        self.key = key
        self.name = name
        self.national_ranking = national_ranking
        self.position = position_abbr(position)
        self.pos_abbr = position
        self.position_ranking = position_ranking
        self.predictions = predictions
        if rating_numerical is not None:
            self.rating_numerical = f"{float(rating_numerical / 100):.4f}"
        else:
            self.rating_numerical = None
        self.rating_stars = rating_stars
        self.recruit_interests = recruit_interests
        self.recruit_interests_url = recruit_interests_url
        self.red_shirt = red_shirt
        self.rivals_ID = rivals_ID
        self.rivals_profile = rivals_profile
        self.rivals_highlights = rivals_highlights
        self.school = school
        self.school_type = school_type
        self.scout_evaluation = scout_evaluation
        self.state = state
        self.state_abbr = state_abbr
        self.state_ranking = state_ranking
        self.thumbnail = thumbnail
        self.twitter = twitter
        self.walk_on = walk_on
        self.weight = str(weight) + " lbs"
        self.year = year


def FootballRecruit(year, name):
    search_results = x247_search = None
    team_ids_raw = process_MySQL(fetch="all", query=TeamIDs)
    team_ids = dict()
    for id in team_ids_raw:
        team_ids.update({id['id']: id['name']})

    if len(name) == 1:
        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}"
        first_name = requests.get(url=x247_search, headers=headers)
        first_name = json.loads(first_name.text)

        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.LastName={name[0]}"
        last_name = requests.get(url=x247_search, headers=headers)
        last_name = json.loads(last_name.text)

        search_results = first_name + last_name
    elif len(name) == 2:
        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}&Player.LastName={name[1]}"

        search_results = requests.get(url=x247_search, headers=headers)
        search_results = json.loads(search_results.text)
    else:
        print(f"Error occurred attempting to create 247sports search URL. Exiting..\n"
              f"{year}\n"
              f"{name}")
        return

    if not search_results:

        raise commands.UserInputError(f"Unable to find [{name[0] if len(name) <= 1 else name[0] + ' ' + name[1]}] in the [{year}] class. Please try again!")

    search_result_players = []

    def correct_commit_string():
        if player['HighestRecruitInterestEventType'] == "HardCommit":
            return "Hard Commit"
        elif player['HighestRecruitInterestEventType'] == "OfficialVisit":
            return None
        elif player['HighestRecruitInterestEventType'] == "0":
            return None
        else:
            return player['HighestRecruitInterestEventType']

    def school_type():
        school_type = soup.find_all(attrs={"data-js": "institution-selector"})

        if not len(school_type) == 0:
            school_type = str(school_type[0].text).strip()
            return school_type
        else:
            return "High School"

    def _247_highlights():
        return player['Player']['Url'] + 'Videos/'

    def early_enrolee():
        icon = soup.find_all(attrs={"class": "icon-time"})

        if icon:
            return True
        else:
            return False

    def early_signee():
        icon = soup.find_all(attrs={"class": "signee-icon"})

        if icon:
            return True
        else:
            return False

    def walk_on():
        icon = soup.find_all(attrs={"class": "icon-walkon"})

        if icon:
            return True
        else:
            return False

    def cb_predictions():
        cbs_raw = soup.find_all("h4")
        cbs = []

        try:
            for item in cbs_raw:
                if item.contents[0] == "Crystal Ball® Predictions":
                    cbs_raw = cbs_raw[1].parent.contents[5]
                    break
        except:
            return False

        for item in cbs_raw:
            if not type(item) == element.NavigableString and "%" in item.text:
                cbs.append(str(item.text).strip())

        return cbs

    def twitter_handle():
        twitter = soup.find_all(attrs={"class": "tweets-comp"})
        try:
            twitter = twitter[0].attrs["data-username"]
            twitter = re.sub(r"[^\w*]+", "", twitter)
            return twitter
        except:
            return "N/A"

    def national_ranking():
        rank = soup.find_all(href="https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool")

        if len(rank) > 1:
            return int(rank[1].contents[3].text)
        else:
            return False

    def state_ranking(player):
        rank = soup.find_all(attrs={"href": f"https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&State={states[player['Hometown']['State']]}"})

        ranking = 0
        try:
            ranking = int(rank[0].contents[3].text)
        except IndexError:
            pass

        if len(rank) == 1:
            return ranking
        else:
            return False

    def position_ranking(player):
        rank = soup.find_all(attrs={"href": f"https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&Position={player['PrimaryPlayerPosition']['Abbreviation']}"})

        ranking = 0
        try:
            ranking = int(rank[0].contents[3].text)
        except IndexError:
            pass

        if len(rank) == 1:
            return ranking
        else:
            return False

    def all_time_ranking():
        rank = soup.find_all(attrs={"href": "https://247sports.com/Sport/Football/AllTimeRecruitRankings/"})

        ranking = 0
        try:
            ranking = rank[1].contents[3].text
        except IndexError:
            pass

        if len(rank) > 1:
            return ranking
        else:
            return False

    # def rivals_profile(player):
    #     # query = f"site:rivals.com/content/prospects/{player['Year']}+{player['Player']['FullName'].replace(' ', '+')}"
    #     query = f"rivals.com {player['Year']} {player['Player']['FullName']}"
    #     results = search(
    #         query=query,
    #         tld="com",
    #         num=10
    #   )
    #     for q in results:
    #         if re.match(r"https://n.rivals.com/content/prospects/[0-9]{4}/\w{1,}-\w{1,}-\d{1,}", q):
    #             return q
    #         else:
    #             return None

    def rivals_ID(profile):
        if profile:
            ID = profile[profile.rfind("-") + 1:]
            return ID
        else:
            return None

    def rivals_highlights(ID):
        return f"https://n.rivals.com/content/prospects/{ID}/featured/videos"

    def recruit_interests():
        req = requests.get(url=player["RecruitInterestsUrl"], headers=headers)
        interests_soup = BeautifulSoup(req.content, "html.parser")

        interests = interests_soup.find_all(attrs={"class": "first_blk"})

        all_interests = []

        for index, interest in enumerate(interests):
            all_interests.append(
                RecruitInterest(
                    school=interest.contents[1].text.strip(),
                    offered="",
                    status=interest.contents[3].text.strip()
                )
            )

        del req
        del interests
        del interests_soup

        return all_interests

    for index, player in enumerate(search_results):
        p = player['Player']

        r = requests.get(url=player['Player']['Url'], headers=headers)
        soup = BeautifulSoup(r.content, "html.parser")

        # TODO Grab all the other variables; red_shirt, rivals_profile, fix the JUCO issue with "NCAA" not showing up and crystal balls if only one team

        team_id = 0
        if player['CommitedInstitutionTeamImage'] is not None:
            team_id = int(player['CommitedInstitutionTeamImage'].split('/')[-1].split('_')[-1].split('.')[0])  # Thank you Psy

        if p['NationalRank'] is None:
            p['NationalRank'] = national_ranking()

        if p['StateRank'] is None:
            p['StateRank'] = state_ranking(p)

        if p['PositionRank'] is None:
            p['PositionRank'] = position_ranking(p)

        # rivals_prof = rivals_profile(player)
        # rivals_id = rivals_ID(rivals_prof)

        search_result_players.append(
            Recruit(
                key=p['Key'],
                name=p['FullName'],
                city=p['Hometown']['City']if p['Hometown']['City'] else 'N/A' ,
                state=p['Hometown']['State'] if p['Hometown']['State'] else 'N/A',
                state_abbr=states[p['Hometown']['State']] if p['Hometown']['State'] else 'N/A',
                height=p['Height'],
                weight=p['Weight'],
                bio=p['Bio'],
                scout_evaluation=p['ScoutEvaluation'],
                x247_profile=p['Url'],
                x247_highlights=_247_highlights(),
                school=p['PlayerHighSchool']['Name'],
                school_type=school_type(),
                position=p['PrimaryPlayerPosition']['Abbreviation'],
                thumbnail=p['DefaultAssetUrl'],
                rating_numerical=p['CompositeRating'],
                rating_stars=p['CompositeStarRating'],
                national_ranking=p['NationalRank'],
                state_ranking=p['StateRank'],
                position_ranking=p['PositionRank'],
                committed=correct_commit_string(),
                committed_school=team_ids[team_id] if team_id > 0 else None,
                commitment_date=player['AnnouncementDate'],
                recruit_interests=recruit_interests(),
                recruit_interests_url=player["RecruitInterestsUrl"],
                year=player['Year'],
                early_enrollee=early_enrolee(),
                early_signee=early_signee(),
                all_time_ranking=all_time_ranking(),
                predictions=cb_predictions(),
                twitter=twitter_handle(),
                walk_on=walk_on(),
                # rivals_profile=rivals_prof,
                # rivals_ID=rivals_id,
                # rivals_highlights=rivals_highlights(rivals_id)
           )
        )

    return search_result_players
