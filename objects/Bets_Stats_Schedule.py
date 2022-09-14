import enum
import logging
import urllib.parse
from datetime import datetime, timedelta, date
from json import JSONEncoder
from typing import Optional, Union

import discord
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from cfbd import ApiClient, BettingApi, GamesApi, Game
from cfbd.rest import ApiException

from helpers.constants import (
    CFBD_CONFIG,
    DEBUGGING_CODE,
    DT_CFBD_GAMES,
    DT_MYSQL_FORMAT,
    DT_STR_FORMAT,
    DT_TBA_TIME,
    HEADERS,
    TZ,
)
from helpers.mysql import (
    processMySQL,
    sqlGetTeamInfoByESPNID,
    sqlGetTeamInfoByID,
    sqlInsertGameBet,
    sqlSelectGameBetbyAuthor,
    sqlSelectGameBetbyOpponent,
    sqlTeamIDs,
    sqlUpdateGameBet,
    SqlFetch,
)
from objects.Exceptions import BettingException, ScheduleException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = [
    "Bet",
    "BetLines",
    "BettingHuskerSchedule",
    "BigTenTeams",
    "FootballTeam",
    "HuskerSched2022",
    "HuskerSchedule",
    "WhichOverUnderChoice",
    "WhichTeamChoice",
    "buildTeam",
    "getConsensusLineByOpponent",
    "getCurrentWeekByOpponent",
    "getHuskerOpponent",
    "getNebraskaGameByOpponent",
    "retrieveGameBets",
]


class SeasonStats:
    losses = None
    wins = None

    def __init__(self, wins: int = 0, losses: int = 0) -> None:
        self.losses: int = losses
        self.wins: int = wins


class HuskerOpponent:
    def __init__(
        self, name, ranking, icon, date_time, week, location, outcome=None
    ) -> None:
        self.date_time = date_time
        self.icon: str = icon
        self.location: str = location
        self.name: str = name
        self.outcome = outcome
        self.ranking = ranking
        self.week: int = week


class HuskerDotComSchedule:
    def __init__(
        self,
        conference,
        game_date_time,
        home,
        icon,
        location,
        opponent_name,
        outcome,
        ranking,
        week,
    ):
        self.conference = conference
        self.game_date_time = game_date_time
        self.home = home
        self.icon = icon
        self.location = location
        self.opponent_name = opponent_name
        self.outcome = outcome
        self.ranking = ranking
        self.week = week


class BigTenTeams(str, enum.Enum):
    Illinois = "Illinois"
    Indiana = "Indiana"
    Iowa = "Iowa"
    Maryland = "Maryland"
    Michigan = "Michigan"
    Michigan_State = "Michigan State"
    Minnesota = "Minnesota"
    Nebraska = "Nebraska"
    Northwestern = "Northwestern"
    Ohio_State = "Ohio State"
    Penn_State = "Penn State"
    Purdue = "Purdue"
    Rutgers = "Rutgers"
    Wisconsin = "Wisconsin"


class HuskerSched2022(str, enum.Enum):
    if datetime.now(tz=TZ).date() <= date(year=2022, month=8, day=27):
        Northwestern = "Northwestern"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=9, day=3):
        North_Dakota = "North Dakota"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=9, day=10):
        Georgia_Southern = "Georgia Southern"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=9, day=17):
        Oklahoma = "Oklahoma"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=10, day=1):
        Indiana = "Indiana"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=10, day=7):
        Rutgers = "Rutgers"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=10, day=15):
        Purdue = "Purdue"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=10, day=29):
        Illinois = "Illinois"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=11, day=5):
        Minnesota = "Minnesota"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=11, day=12):
        Michigan = "Michigan"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=11, day=19):
        Wisconsin = "Wisconsin"

    if datetime.now(tz=TZ).date() <= date(year=2022, month=11, day=25):
        Iowa = "Iowa"

    def __str__(self) -> str:
        _game_dates: tuple[date, ...] = (
            date(year=2022, month=8, day=27),
            date(year=2022, month=9, day=3),
            date(year=2022, month=9, day=10),
            date(year=2022, month=9, day=17),
            date(year=2022, month=10, day=1),
            date(year=2022, month=10, day=7),
            date(year=2022, month=10, day=15),
            date(year=2022, month=10, day=29),
            date(year=2022, month=11, day=5),
            date(year=2022, month=11, day=12),
            date(year=2022, month=11, day=19),
            date(year=2022, month=11, day=25),
        )

        teams: list[str] = [
            entry.value  # noqa
            for entry in HuskerSched2022
            if isinstance(entry.value, str)  # noqa
        ]
        game_index: int = teams.index(str(self.value))
        game_date: str = f"{_game_dates[game_index]}"

        return f"{str(self.value)}__{game_date}"


class BettingHuskerSchedule(str, enum.Enum):
    Northwestern = "Northwestern"
    North_Dakota = "North Dakota"
    Georgia_Southern = "Georgia Southern"
    Oklahoma = "Oklahoma"
    Indiana = "Indiana"
    Rutgers = "Rutgers"
    Purdue = "Purdue"
    Illinois = "Illinois"
    Minnesota = "Minnesota"
    Michigan = "Michigan"
    Wisconsin = "Wisconsin"
    Iowa = "Iowa"


class WhichTeamChoice(str, enum.Enum):
    Nebraska = "Nebraska"
    Opponent = "Opponent"
    NA = "Not Available"

    def __str__(self) -> str:
        return str(self.value)


class WhichOverUnderChoice(str, enum.Enum):
    Over = "Over"
    Under = "Under"
    NA = "Not Available"

    def __str__(self) -> str:
        return str(self.value)


class BetLines:
    __slots__ = [
        "pointsOpen",
        "points",
        "spreadOpen",
        "formattedSpread",
    ]

    def __init__(self, from_dict: dict) -> None:
        self.formattedSpread = None
        self.points = None
        self.pointsOpen = None
        self.spreadOpen = None

        from_dict["points"] = from_dict["overUnder"]
        from_dict["pointsOpen"] = from_dict["overUnderOpen"]

        for key, value in from_dict.items():
            try:
                setattr(self, key, value)
            except AttributeError as _err:
                continue

    def __str__(self) -> str:
        return (
            f"Against the Spread: {self.formattedSpread} (Opened: {self.spreadOpen})\n"
            f"Total Points: {self.points} (Opened: {self.pointsOpen})"
        )

    def __repr__(self) -> str:
        return str([var for var in vars()])


class FootballTeam(JSONEncoder):
    __slots__ = [
        "alt_name",
        "city",
        "color",
        "conference",
        "division",
        "id_str",
        "logo",
        "school_name",
        "stadium",
        "state",
    ]

    def __init__(self, from_dict: dict = Optional[dict], *args, **kwargs) -> None:
        super().__init__()
        if from_dict:
            from_dict["city"] = from_dict["location_city"]
            from_dict["id_str"] = from_dict["id"]
            from_dict["logo"] = from_dict["logos1"]
            from_dict["school_name"] = from_dict["school"]
            from_dict["stadium"] = from_dict["location_name"]
            from_dict["state"] = from_dict["location_state"]

            for key, value in from_dict.items():
                try:
                    setattr(self, key, value)
                except AttributeError as _err:
                    del key
                    continue
        else:
            self.alt_name: Optional[str] = kwargs.get("alt_name", None)
            self.city: Optional[str] = kwargs.get("city", None)
            self.conference: Optional[str] = kwargs.get("conference", None)
            self.division: Optional[str] = kwargs.get("division", None)
            self.id_str: Optional[str] = kwargs.get("id_str", None)
            self.logo: Optional[str] = kwargs.get("logo", None)
            self.school_name: Optional[str] = kwargs.get("school_name", None)
            self.stadium: Optional[str] = kwargs.get("stadium", None)
            self.state: Optional[str] = kwargs.get("state", None)

    def __str__(self) -> str:
        return f"{self.school_name}".title()


class Bet:
    __slots__ = [
        "_raw",
        "author",
        "author_str",
        "bet_lines",
        "created",
        "created_str",
        "game_datetime",
        "game_datetime_passed",
        "home_game",
        "opponent_name",
        "predict_game",
        "predict_points",
        "predict_spread",
        "resolved",
        "week",
    ]

    def __init__(
        self,
        author: Union[discord.Member, discord.User],
        opponent_name: Union[BigTenTeams, HuskerSched2022],
        predict_game: Optional[WhichTeamChoice],
        predict_points: Optional[WhichOverUnderChoice],
        predict_spread: Optional[WhichTeamChoice],
    ) -> None:
        logger.debug("Creating a Bet object")

        self._raw = getNebraskaGameByOpponent(opponent_name)
        self.author: discord.Member = author
        self.author_str: str = f"{self.author.name}#{self.author.discriminator}"
        self.created: datetime = datetime.now(tz=TZ)
        self.created_str: str = str(self.created)
        self.game_datetime: Optional[datetime] = datetime.strptime(
            self._raw.start_date, DT_CFBD_GAMES
        ).astimezone(tz=TZ)
        self.game_datetime_passed: bool = (
            datetime.now(tz=TZ) >= self.game_datetime or False
        )
        self.home_game: bool = (
            True if self._raw.home_team == BigTenTeams.Nebraska else False
        )
        self.opponent_name = buildTeam(id_str=getTeamIdByName(opponent_name))
        self.resolved: bool = False
        self.week = self._raw.week
        self.predict_game = predict_game
        self.predict_points = predict_points
        self.predict_spread = predict_spread

        if self.home_game:
            self.bet_lines: BetLines = getConsensusLineByOpponent(
                away_team=self.opponent_name.school_name.lower(),
                home_team=BigTenTeams.Nebraska.lower(),
            )
        else:
            self.bet_lines: BetLines = getConsensusLineByOpponent(
                away_team=BigTenTeams.Nebraska.lower(),
                home_team=self.opponent_name.school_name.lower(),
            )

    def __str__(self) -> str:
        return f"{self.author_str}: Wins-{self.predict_game}, OverUnder-{self.predict_points}, Spread-{self.predict_spread}"

    def submitRecord(self) -> None:
        logger.debug("Submitting MySQL entry for bet")
        previous_bet = retrieveGameBets(
            author_str=self.author_str, school_name=self.opponent_name.school_name
        )

        if previous_bet:
            if (
                previous_bet["predict_game"] == self.predict_game
                and previous_bet["predict_points"] == self.predict_points
                and previous_bet["predict_spread"] == self.predict_spread
            ):
                logger.debug("Previous bet matches current bet")
                return
            else:
                logger.debug("Updating previously entered bet")
                try:
                    processMySQL(
                        query=sqlUpdateGameBet,
                        values=(
                            self.predict_game,
                            self.predict_points,
                            self.predict_spread,
                            self.created,
                            self.created_str,
                            previous_bet["id"],
                        ),
                    )
                except BettingException:
                    BettingException("Was not able to create bet in MySQL database.")
        else:
            logger.debug("Embedded placed")
            try:
                processMySQL(
                    query=sqlInsertGameBet,
                    values=(
                        self.author,
                        self.author_str,
                        self.created,
                        self.created_str,
                        self.opponent_name.school_name,
                        self.home_game,
                        self.week,
                        self.game_datetime.strftime(DT_MYSQL_FORMAT),
                        self.game_datetime_passed,
                        self.predict_game,
                        self.predict_points,
                        self.predict_spread,
                        self.resolved,
                    ),
                )
            except BettingException:
                BettingException("Was not able to create bet in MySQL database.")


def retrieveGameBets(
    school_name: str, author_str: str = None, _all: bool = False
) -> Union[list[dict], dict, None]:
    logger.info(
        f"Looking to see if a bet already exists for {author_str} and {school_name}"
    )
    if author_str:
        results = processMySQL(
            query=sqlSelectGameBetbyAuthor,
            values=(author_str, school_name),
            fetch=SqlFetch.one,
            # fetch="one",
        )
    else:
        results = processMySQL(
            query=sqlSelectGameBetbyOpponent,
            values=school_name,
            fetch=SqlFetch.all,
        )
    if results:
        if _all:
            return results
        else:
            return results
    else:
        return None


def getNebraskaGameByOpponent(opponent_name: str, year=datetime.now().year) -> Game:
    logger.info(f"Getting Nebraska opponent_name by name: {opponent_name}")

    cfbd_api = GamesApi(ApiClient(CFBD_CONFIG))
    nebraska = BigTenTeams.Nebraska.lower()

    game = [
        game
        for game in cfbd_api.get_games(year=year, team=nebraska)
        if (
            game.home_team.lower() == nebraska.lower()
            and game.away_team.lower() == opponent_name.lower()
        )
        or (
            game.home_team.lower() == opponent_name.lower()
            and game.away_team.lower() == nebraska.lower()
        )
    ]
    logger.debug(
        f"Found game {game[0].id} with {game[0].away_team} and {game[0].home_team}"
    )
    return game[0]


def getTeamIdByName(team_name: str) -> str:
    logger.info(f"Getting Team ID by Name: {team_name}")

    sql_teams = processMySQL(
        query=sqlTeamIDs,
        fetch=SqlFetch.all,
        # fetch="all",
    )
    _id = ""

    if team_name.lower() in [team["school"].lower() for team in sql_teams]:
        for team in sql_teams:
            if team["school"] == team_name:
                _id = team["id"]
                break
    else:
        raise BettingException(
            f"Not able to locate {team_name} in team list. Try again!"
        )

    if _id:
        return _id
    else:
        raise BettingException(
            f"Not able to locate {team_name} in team list. Try again!"
        )


def buildTeam(id_str: str) -> FootballTeam:
    logger.debug("Building a FootballTeam")

    query: dict = processMySQL(
        query=sqlGetTeamInfoByID,
        fetch=SqlFetch.one,
        # fetch="one",
        values=id_str,
    )
    if query is None:
        query: dict = processMySQL(
            query=sqlGetTeamInfoByESPNID,
            fetch=SqlFetch.one,
            # fetch="one",
            values=id_str,
        )

    if query:
        return FootballTeam(from_dict=query)
    else:
        raise BettingException("Unable to create FootballTeam because query is None.")


def getConsensusLineByOpponent(
    away_team: str,
    home_team: str,
    year: int = datetime.now().year,
) -> Optional[BetLines]:
    logger.info(
        f"Getting the consensus line for {year} {away_team} and {home_team} game"
    )

    betting_api = BettingApi(ApiClient(CFBD_CONFIG))

    try:
        api_response = betting_api.get_lines(away=away_team, home=home_team, year=year)
    except (ApiException, TypeError):
        return None

    logger.debug(f"Results: {api_response}")
    try:
        lines = api_response[0].lines[0]
    except IndexError:
        return None

    return BetLines(from_dict=lines)


def collect_opponent(game, year, week) -> Union[HuskerOpponent, str]:
    # This is the culmination of going line by line through Huskers.com HTML and CSS.
    # If the website changes, this will more than likely need to change.
    logger.info(f"Collecting opponent_name information for Week {week} {year}")
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

    soup: BeautifulSoup = BeautifulSoup(reqs.content, "html.parser")
    games_raw: ResultSet = soup.find_all(attrs={"class": "sidearm-schedule-game"})

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

        _opponent_name = collect_opponent(game, year, week)
        if _opponent_name == "Unknown Opponent":  # What am I doing here?
            continue

        if "TBA" in _opponent_name.date_time:
            # Specific time to reference later for TBA games
            gdt_string = f"{_opponent_name.date_time[0:6]} {year} {DT_TBA_TIME}"
            _opponent_name.date_time = datetime.strptime(
                gdt_string, DT_STR_FORMAT
            ).astimezone(tz=TZ)
        else:
            if "or" in str(_opponent_name.date_time).lower():
                temp = str(_opponent_name.date_time).split(" or ")
                if ":" in temp[0]:
                    _opponent_name.date_time = f"{temp[0]} {temp[1][-3:]}"
                else:
                    _opponent_name.date_time = f"{temp[0]}:00 {temp[1][-3:]}"

            _opponent_name.date_time = datetime.strptime(
                _opponent_name.date_time.replace("A.M.", "AM")
                .replace("a.m.", "AM")
                .replace("P.M.", "PM")
                .replace("p.m.", "PM"),
                DT_STR_FORMAT,
            ).astimezone(tz=TZ)
            _opponent_name.date_time += timedelta(hours=1)

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
        conference: bool = _opponent_name.name in conference_teams
        home: bool = "Lincoln, Neb." in _opponent_name.location

        games.append(
            HuskerDotComSchedule(
                location=_opponent_name.location,
                opponent_name=_opponent_name.name,
                outcome=_opponent_name.outcome,
                icon=_opponent_name.icon,
                ranking=_opponent_name.ranking,
                week=_opponent_name.week,
                game_date_time=_opponent_name.date_time,
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


def getCurrentWeekByOpponent(team: str, year: int = datetime.now().year) -> int:
    logger.info(f"Getting the current week for the {year} {team} game")
    games_api = GamesApi(ApiClient(CFBD_CONFIG))

    try:
        games = games_api.get_games(
            year=year, team=BigTenTeams.Nebraska.lower()
        )  # We only care about Nebraska's schedule
    except ApiException:
        logger.exception("CFBD API unable to get games", exc_info=True)
        raise BettingException("CFBD API unable to get games")

    for index, game in enumerate(games):
        logger.info(f"Checking the Week {game.week} game.")
        if team.lower() == BigTenTeams.Nebraska:
            if game.week == games[1].week:  # Week 0 game
                return 0

            if not (game.away_points and game.home_points):
                return game.week
            else:
                logger.exception(
                    "Unknown error occurred when getting week for Nebraska game",
                    exc_info=True,
                )
        elif (
            game.away_team.lower() == BigTenTeams.Nebraska.lower()
            or game.home_team.lower() == BigTenTeams.Nebraska.lower()
        ) and (
            game.away_team.lower() == team.lower()
            or game.home_team.lower() == team.lower()
        ):
            return game.week

    logger.exception(f"Unable to find week for {team}")
    raise BettingException(f"Unable to find week for {team}")


def getHuskerOpponent(_game: Game) -> dict[str, str]:
    if _game.away_team.lower() == BigTenTeams.Nebraska.lower():
        return {"opponent_name": _game.home_team, "id": str(_game.home_id)}
    elif _game.home_team.lower() == BigTenTeams.Nebraska.lower():
        return {"opponent_name": _game.away_team, "id": str(_game.away_id)}


logger.info(f"{str(__name__).title()} module loaded!")
