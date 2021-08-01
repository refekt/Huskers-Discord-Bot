import datetime
import platform

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from objects.Bets import GameBetInfo
from utilities.constants import HEADERS, TZ


class SeasonStats:
    wins = None
    losses = None

    def __init__(self, wins=0, losses=0):
        self.wins = wins
        self.losses = losses


class HuskerOpponent:
    name = None
    ranking = None
    icon = None
    date_time = None
    conference = None

    def __init__(self, name, ranking, icon, date_time, conference):
        self.name = name
        self.ranking = ranking
        self.icon = icon
        self.date_time = date_time
        self.conference = conference


class HuskerDotComSchedule:
    bets = GameBetInfo
    location = None
    opponent = None
    outcome = None
    ranking = None
    week = None
    game_date_time = None
    game_date_time_dt = None

    def __init__(self, bets, location, opponent, outcome, ranking, week, game_date_time, game_date_time_dt=None):
        self.bets = bets
        self.location = location
        self.opponent = opponent
        self.outcome = outcome
        self.ranking = ranking
        self.week = week
        self.game_date_time = game_date_time
        self.game_date_time_dt = game_date_time_dt


def HuskerSchedule(sport: str, year=datetime.datetime.now().year):
    reqs = requests.get(url=f"https://huskers.com/sports/{sport}/schedule/{year}", headers=HEADERS)

    if not reqs.status_code == 200:
        raise ConnectionError("Unable to retrieve schedule from Huskers.com.")

    def collect_opponent(game):
        # This is the cumulation of going line by line through Huskers.com HTML and CSS.
        # If the website changes, this will more than likely need to change.
        try:
            name = game.contents[1].contents[3].contents[3].contents[3].text.strip().replace("\n", " ")
            icon = "https://huskers.com" + game.contents[1].contents[1].contents[1].attrs["data-src"]
            _date = game.contents[1].contents[3].contents[1].contents[1].contents[1].text.strip()
            _time = game.contents[1].contents[3].contents[1].contents[1].contents[3].text.strip()

            if "(" in _time:
                _time = "TBA"

            if ":" not in _time:
                _time = _time.replace(" ", ":00 ")
            date_time = f"{_date[0:6]} {year} {_time}"
            if "Noon" in date_time:  # I blame Iowa
                date_time = date_time.replace("Noon", "12:00 P.M.")
            conference = game.contents[1].contents[3].contents[1].contents[3]
            if len(conference.contents) > 1:
                conference = conference.contents[1].text.strip()
            else:
                conference = "Non-Con"

            return HuskerOpponent(
                name=name,
                ranking=None,
                icon=icon,
                date_time=date_time,
                conference=conference,
            )
        except IndexError:
            return "Unknown Opponent"

    soup = BeautifulSoup(reqs.content, "html.parser")
    games_raw = soup.find_all(attrs={"class": "sidearm-schedule-games-container"})
    games_raw = [game for game in games_raw[0].contents if type(game) == Tag]  # Remove all NavigableStrings from the list

    # Some games have a box around them and this removes that.
    for index, game in enumerate(games_raw):
        if len(game.attrs) == 0:
            games_raw[index] = game.contents[1].contents[3].contents[1]

    games = []
    season_stats = SeasonStats()
    exempt_games = ("Spring Game", "Fan Day")
    special_games = ("Homecoming", "Bowl")
    week = 0

    for game in games_raw:
        week += 1

        # Don't include scrimages and other "games" in the week count
        if any(g in game.text for g in exempt_games):
            week -= 1
            continue

        # 31 July 2021: Removed this because I think it's redundant. Taken care of earlier by removing box.
        # if any(g in game.text for g in special_games):
        #     g = game.contents[1].contents[3].contents[1].contents[1]
        # else:
        #     g = game.contents[1]

        location = game.contents[3].contents[1].text.strip()
        opponent = collect_opponent(game)

        if "Canceled" in game.contents[5].contents[1].text:
            outcome = "Canceled"
        else:
            try:
                outcome = f"{game.contents[5].contents[1].contents[3].text.strip()} {game.contents[5].contents[1].contents[5].text}"

                if game.contents[5].contents[1].contents[1].text.strip():
                    outcome = game.contents[5].contents[1].contents[1].text.strip() + " " + outcome
            except IndexError:
                outcome = ""

        if "TBA" in opponent.date_time:
            gdt_string = f"{opponent.date_time[0:6]} {year} 10:58 PM"
            game_date_time = datetime.datetime.strptime(gdt_string, "%b %d %Y %I:%M %p").astimezone(tz=TZ)
        else:
            game_date_time = datetime.datetime.strptime(opponent.date_time.replace("A.M.", "AM").replace("P.M.", "PM"), "%b %d %Y %I:%M %p").astimezone(tz=TZ)
            game_date_time += datetime.timedelta(hours=1)

        # 31 July 2021: May be no longer needed. Was used to offset time zones
        # if "Linux" in platform.platform():
        #     offset = 0
        #     game_date_time += datetime.timedelta(hours=offset)

        games.append(
            HuskerDotComSchedule(
                bets=None,
                location=location,
                opponent=opponent,
                outcome=outcome,
                ranking=None,
                week=week,
                game_date_time=game_date_time
            )
        )

    for game in games:
        if "W" in game.outcome:
            season_stats.wins += 1
        elif "L" in game.outcome:
            season_stats.losses += 1
        else:
            pass

    return games, season_stats

# def Venue():
#     r = requests.get("https://api.collegefootballdata.com/venues")
#     return r.json()
