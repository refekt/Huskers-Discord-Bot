import urllib.parse
from datetime import datetime, timedelta
from typing import Union

import requests
from bs4 import BeautifulSoup

from helpers.constants import HEADERS, DT_TBA_TIME, DT_STR_FORMAT, TZ
from objects.Exceptions import ScheduleException
from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["HuskerSchedule"]

logger.info(f"{str(__name__).title()} module loaded!")


class SeasonStats:
    losses = None
    wins = None

    def __init__(self, wins=0, losses=0):
        self.losses = losses
        self.wins = wins


class HuskerOpponent:
    def __init__(self, name, ranking, icon, date_time, week, location, outcome=None):
        self.date_time = date_time
        self.icon = icon
        self.location = location
        self.name = name
        self.outcome = outcome
        self.ranking = ranking
        self.week = week


class HuskerDotComSchedule:
    def __init__(
        self,
        conference,
        game_date_time,
        home,
        icon,
        location,
        opponent,
        outcome,
        ranking,
        week,
    ):
        self.conference = conference
        self.game_date_time = game_date_time
        self.home = home
        self.icon = icon
        self.location = location
        self.opponent = opponent
        self.outcome = outcome
        self.ranking = ranking
        self.week = week


def collect_opponent(game, year, week) -> Union[HuskerOpponent, str]:
    # This is the culmination of going line by line through Huskers.com HTML and CSS.
    # If the website changes, this will more than likely need to change.
    logger.info(f"Collecting opponent information for Week {week} {year}")
    game = game.contents[1]
    try:
        name = (
            game.contents[1]
            .contents[3]
            .contents[3]
            .contents[3]
            .text.strip()
            .replace("\n", " ")
        )

        ranking = None

        if "#" in name:
            try:
                [ranking, name] = str(name).split(" ", maxsplit=1)
            except ValueError:
                pass

        location = game.contents[3].contents[1].text.strip().replace("\n", " ")

        if "Buy Tickets" in location:
            location = location.split("Buy Tickets ")[1].replace(
                " Memorial Stadium", ""
            )

        temp = game.contents[1].contents[1].contents[1].attrs["data-src"]
        icon = None

        if "://" in temp:  # game.contents[1].contents[1].contents[1].attrs["data-src"]:
            # icon = temp_icon
            try:
                url_parser = urllib.parse.urlparse(temp)
                icon = f"{url_parser.scheme}://{url_parser.netloc}{urllib.parse.quote(url_parser.path)}"
            except:  # noqa
                pass
        else:
            icon = (
                "https://huskers.com"
                + game.contents[1].contents[1].contents[1].attrs["data-src"]
            )

        _date = (
            game.contents[1]
            .contents[3]
            .contents[1]
            .contents[1]
            .contents[1]
            .text.strip()
        )

        _time = (
            game.contents[1]
            .contents[3]
            .contents[1]
            .contents[1]
            .contents[3]
            .text.strip()
        )

        if "Canceled" in game.contents[5].contents[1].text:
            outcome = "Canceled"
        else:
            try:
                outcome = f"{game.contents[5].contents[1].contents[3].text.strip()} {game.contents[5].contents[1].contents[5].text}"

                if game.contents[5].contents[1].contents[1].text.strip():
                    outcome = (
                        game.contents[5].contents[1].contents[1].text.strip()
                        + " "
                        + outcome
                    )
            except IndexError:
                outcome = ""

        if _time == "Noon":
            _time = _time.replace("Noon", "12:00 PM")

        if ":" not in _time:
            _time = _time.replace(" ", ":00 ")

        date_time = f"{_date[0:6]} {year} {_time}"
        del _date, _time

        return HuskerOpponent(
            name=name,
            ranking=ranking,
            icon=icon,
            date_time=date_time,
            week=week,
            location=location,
            outcome=outcome,
        )
    except IndexError:
        return "Unknown Opponent"


def HuskerSchedule(
    year=datetime.now().year,
) -> tuple[list[HuskerDotComSchedule], SeasonStats]:
    logger.info(f"Creating Husker schedule for '{year}'")

    reqs = requests.get(
        url=f"https://huskers.com/sports/football/schedule/{year}", headers=HEADERS
    )

    assert reqs.status_code == 200, ScheduleException(
        "Unable to retrieve schedule from Huskers.com."
    )

    soup = BeautifulSoup(reqs.content, "html.parser")
    games_raw = soup.find_all(attrs={"class": "sidearm-schedule-game"})

    # Some games have a box around them and this removes that
    for index, game in enumerate(games_raw):
        if len(game.attrs) == 0:
            games_raw[index] = game.contents[1].contents[3].contents[1]

    del index, game

    games = []
    season_stats = SeasonStats()
    week = 0

    for game in games_raw:
        week += 1

        opponent = collect_opponent(game, year, week)
        if opponent == "Unknown Opponent":  # TODO What am I doing here?
            continue

        if "TBA" in opponent.date_time:
            # Specific time to reference later for TBA games
            gdt_string = f"{opponent.date_time[0:6]} {year} {DT_TBA_TIME}"
            opponent.date_time = datetime.strptime(
                gdt_string, DT_STR_FORMAT
            ).astimezone(tz=TZ)
        else:
            if "or" in str(opponent.date_time).lower():
                temp = str(opponent.date_time).split(" or ")
                if ":" in temp[0]:
                    opponent.date_time = f"{temp[0]} {temp[1][-3:]}"
                else:
                    opponent.date_time = f"{temp[0]}:00 {temp[1][-3:]}"

            opponent.date_time = datetime.strptime(
                opponent.date_time.replace("A.M.", "AM")
                .replace("a.m.", "AM")
                .replace("P.M.", "PM")
                .replace("p.m.", "PM"),
                DT_STR_FORMAT,
            ).astimezone(tz=TZ)
            opponent.date_time += timedelta(hours=1)

        conference_teams = (
            "Illinois",
            "Iowa",
            "Maryland",
            "Michigan State",
            "Michigan",
            "Minnesota",
            "Northwestern",
            "Ohio State",
            "Penn State",
            "Purdue",
            "Rutgers",
            "Wisconsin",
        )
        conference: bool = opponent.name in conference_teams
        home: bool = "Lincoln, Neb." in opponent.location

        games.append(
            HuskerDotComSchedule(
                location=opponent.location,
                opponent=opponent.name,
                outcome=opponent.outcome,
                icon=opponent.icon,
                ranking=opponent.ranking,
                week=opponent.week,
                game_date_time=opponent.date_time,
                conference=conference,
                home=home,
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
