import requests

from utilities.constants import HEADERS


class GameBets:
    game_number = None
    over_under = None
    spread = None
    win = None

    def __init__(self, game_number, over_under, spread, win):
        self.game_number = game_number
        self.over_under = over_under
        self.spread = spread
        self.win = win


class GameBetLine:
    provider = None
    spread = None
    formatted_spread = None
    over_under = None

    def __init__(self, provider=None, spread=None, formatted_spread=None, over_under=None):
        self.provider = provider
        self.spread = spread
        self.formatted_spread = formatted_spread
        self.over_under = over_under


class GameBetInfo:
    home_team = None
    home_score = None
    away_team = None
    away_score = None
    userbets = []
    lines = []

    def __init__(self, year, week, team, season="regular"):  # , home_team=None, home_score=None, away_team=None, away_score=None, lines=None):
        self.home_team = None
        self.home_score = None
        self.away_team = None
        self.away_score = None
        self.userbets = []
        self.lines = []

        self.establish(year, week, team, season)

    def establish(self, year, week, team, season="regular"):
        url = f"https://api.collegefootballdata.com/lines?year={year}&week={week}&seasonType={season}&team={team}"
        re = requests.get(url=url, headers=HEADERS)
        data = re.json()

        try:
            self.home_team = data[0]['homeTeam']
            self.home_score = data[0]['homeScore']
            self.away_team = data[0]['awayTeam']
            self.away_score = data[0]['awayScore']
            linedata = data[0]["lines"]

            for line in linedata:
                self.lines.append(
                    GameBetLine(
                        provider=line['provider'],
                        spread=line['spread'],
                        formatted_spread=line['formattedSpread'],
                        over_under=line['overUnder']
                    )
                )
        except:
            pass
