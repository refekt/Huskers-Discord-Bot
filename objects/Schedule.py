# TODO
# * Modernize and revamp
# TODO

# import datetime
#
# import requests
# from bs4 import BeautifulSoup
#
# from utilities.constants import DT_STR_FORMAT, DT_TBA_TIME, HEADERS, TZ
#
#
# class SeasonStats:
#     wins = None
#     losses = None
#
#     def __init__(self, wins=0, losses=0):
#         self.wins = wins
#         self.losses = losses
#
#
# class HuskerOpponent:
#     def __init__(self, name, ranking, icon, date_time, week, location, outcome=None):
#         self.name = name
#         self.ranking = ranking
#         self.icon = icon
#         self.date_time = date_time
#         self.week = week
#         self.location = location
#         self.outcome = outcome
#
#
# class HuskerDotComSchedule:
#     def __init__(
#         self,
#         location,
#         opponent,
#         icon,
#         outcome,
#         ranking,
#         week,
#         game_date_time,
#         home,
#         conference,
#     ):
#         self.location = location
#         self.opponent = opponent
#         self.icon = icon
#         self.outcome = outcome
#         self.ranking = ranking
#         self.week = week
#         self.game_date_time = game_date_time
#         self.home = home
#         self.conference = conference
#
#
# def collect_opponent(game, year, week):
#     # This is the culmination of going line by line through Huskers.com HTML and CSS.
#     # If the website changes, this will more than likely need to change.
#     game = game.contents[1]
#     try:
#         name = (
#             game.contents[1]
#             .contents[3]
#             .contents[3]
#             .contents[3]
#             .text.strip()
#             .replace("\n", " ")
#         )
#         ranking = None
#         if "#" in name:
#             try:
#                 [ranking, name] = str(name).split(" ", maxsplit=1)
#             except ValueError:
#                 pass
#         location = game.contents[3].contents[1].text.strip().replace("\n", " ")
#         if "Buy Tickets" in location:
#             location = location.split("Buy Tickets ")[1].replace(
#                 " Memorial Stadium", ""
#             )
#         icon = (
#             "https://huskers.com"
#             + game.contents[1].contents[1].contents[1].attrs["data-src"]
#         )
#         _date = (
#             game.contents[1]
#             .contents[3]
#             .contents[1]
#             .contents[1]
#             .contents[1]
#             .text.strip()
#         )
#         _time = (
#             game.contents[1]
#             .contents[3]
#             .contents[1]
#             .contents[1]
#             .contents[3]
#             .text.strip()
#         )
#
#         if "Canceled" in game.contents[5].contents[1].text:
#             outcome = "Canceled"
#         else:
#             try:
#                 outcome = f"{game.contents[5].contents[1].contents[3].text.strip()} {game.contents[5].contents[1].contents[5].text}"
#
#                 if game.contents[5].contents[1].contents[1].text.strip():
#                     outcome = (
#                         game.contents[5].contents[1].contents[1].text.strip()
#                         + " "
#                         + outcome
#                     )
#             except IndexError:
#                 outcome = ""
#
#         # if "(" in _time:
#         #     _time = "TBA"
#
#         if _time == "Noon":
#             _time = _time.replace("Noon", "12:00 PM")
#
#         if ":" not in _time:
#             _time = _time.replace(" ", ":00 ")
#
#         date_time = f"{_date[0:6]} {year} {_time}"
#         del _date, _time
#
#         # if len(conference.contents) > 1:
#         #     conference = conference.contents[1].text.strip()
#         # else:
#         #     conference = "Non-Con"
#
#         return HuskerOpponent(
#             name=name,
#             ranking=ranking,
#             icon=icon,
#             date_time=date_time,
#             week=week,
#             location=location,
#             outcome=outcome,
#         )
#     except IndexError:
#         return "Unknown Opponent"
#
#
# def HuskerSchedule(sport: str, year=datetime.datetime.now().year):
#     reqs = requests.get(
#         url=f"https://huskers.com/sports/{sport}/schedule/{year}", headers=HEADERS
#     )
#
#     if not reqs.status_code == 200:
#         raise ConnectionError("Unable to retrieve schedule from Huskers.com.")
#
#     soup = BeautifulSoup(reqs.content, "html.parser")
#     games_raw = soup.find_all(attrs={"class": "sidearm-schedule-game"})
#
#     # Some games have a box around them and this removes that
#     for index, game in enumerate(games_raw):
#         if len(game.attrs) == 0:
#             games_raw[index] = game.contents[1].contents[3].contents[1]
#
#     del index, game
#
#     games = []
#     season_stats = SeasonStats()
#     week = 0
#
#     for game in games_raw:
#         week += 1
#
#         opponent = collect_opponent(game, year, week)
#         if opponent == "Unknown Opponent":
#             continue
#
#         if "TBA" in opponent.date_time:
#             # Specific time to reference later for TBA games
#             gdt_string = f"{opponent.date_time[0:6]} {year} {DT_TBA_TIME}"
#             opponent.date_time = datetime.datetime.strptime(
#                 gdt_string, DT_STR_FORMAT
#             ).astimezone(tz=TZ)
#         else:
#             opponent.date_time = datetime.datetime.strptime(
#                 opponent.date_time.replace("A.M.", "AM")
#                 .replace("a.m.", "AM")
#                 .replace("P.M.", "PM")
#                 .replace("p.m.", "PM"),
#                 DT_STR_FORMAT,
#             ).astimezone(tz=TZ)
#             opponent.date_time += datetime.timedelta(hours=1)
#
#         teams = (
#             "Illinois",
#             "Michigan State",
#             "Northwestern",
#             "Minnesota",
#             "Purdue",
#             "Ohio State",
#             "Wisconsin",
#             "Iowa",
#             "Michigan",
#             "Maryland",
#             "Rutgers",
#             "Penn State",
#         )
#         conf = opponent.name in teams
#         home = "Lincoln, Neb." in opponent.location
#
#         games.append(
#             HuskerDotComSchedule(
#                 location=opponent.location,
#                 opponent=opponent.name,
#                 outcome=opponent.outcome,
#                 icon=opponent.icon,
#                 ranking=opponent.ranking,
#                 week=opponent.week,
#                 game_date_time=opponent.date_time,
#                 conference=conf,
#                 home=home,
#             )
#         )
#
#     for game in games:
#         if "W" in game.outcome:
#             season_stats.wins += 1
#         elif "L" in game.outcome:
#             season_stats.losses += 1
#         else:
#             pass
#
#     return games, season_stats
