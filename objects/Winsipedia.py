import logging
from typing import Union

import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet

from helpers.constants import HEADERS
from objects.Exceptions import StatsException
from objects.Logger import discordLogger, is_debugging

logger = discordLogger(
    name=__name__, level=logging.DEBUG if is_debugging() else logging.INFO
)

__all__: list[str] = [
    "CompareWinsipedia",
    "CompareWinsipediaTeam",
    "TeamStatsWinsipediaTeam",
]


class TeamStatsWinsipediaTeam:
    def __init__(self, *, team_name: str) -> None:
        def all_time_record() -> Union[tuple[str, str], str]:
            atr: ResultSet = soup.find_all(attrs={"class": "ranking span2 item2"})
            try:
                return (
                    atr[0].contents[1].contents[3].contents[1].text,
                    atr[0].contents[3].contents[1].text.strip(),
                )
            except:  # noqa
                return "UNK", "UNK"

        def championships() -> Union[tuple[str, str], str]:
            champs: ResultSet = soup.find_all(attrs={"class": "ranking span2 item3"})
            try:
                return (
                    champs[0].contents[3].contents[1].text,
                    champs[0].contents[5].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def conf_championships() -> Union[tuple[str, str], str]:
            conf: ResultSet = soup.find_all(attrs={"class": "ranking span2 item4h"})
            try:
                return (
                    conf[0].contents[3].contents[1].text,
                    conf[0].contents[5].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def bowl_games() -> (str, str):
            bowl: ResultSet = soup.find_all(attrs={"class": "ranking span2 item5h"})
            try:
                return (
                    bowl[0].contents[1].contents[1].text,
                    bowl[0].contents[3].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def all_time_wins() -> Union[tuple[str, str], str]:
            atw: ResultSet = soup.find_all(attrs={"class": "ranking span2 item1"})
            try:
                return (
                    atw[0].contents[1].contents[1].text,
                    atw[0].contents[3].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def bowl_record() -> Union[tuple[str, str], str]:
            bowl: ResultSet = soup.find_all(attrs={"class": "ranking span2 item2"})
            try:
                return (
                    bowl[1].contents[1].contents[3].contents[1].text,  # \n and \t
                    bowl[1].contents[3].contents[1].text.strip(),
                )
            except:  # noqa
                return "UNK", "UNK"

        def consensus_all_americans() -> Union[tuple[str, str], str]:
            caa: ResultSet = soup.find_all(attrs={"class": "ranking span2 item3"})
            try:
                return (
                    caa[1].contents[1].contents[1].text,
                    caa[1].contents[3].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def heisman_winners() -> Union[tuple[str, str], str]:
            hw: ResultSet = soup.find_all(attrs={"class": "ranking span2 item4"})
            try:
                return (
                    hw[1].contents[3].contents[1].text,
                    hw[1].contents[5].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def nfl_draft_picks() -> Union[tuple[str, str], str]:
            nfl_picks: ResultSet = soup.find_all(attrs={"class": "ranking span2 item5"})
            try:
                return (
                    nfl_picks[1].contents[3].contents[1].text,
                    nfl_picks[1].contents[5].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        def weeks_ap_poll() -> Union[tuple[str, str], str]:
            ap_poll: ResultSet = soup.find_all(attrs={"class": "ranking span2 item6"})
            try:
                return (
                    ap_poll[0].contents[3].contents[1].text,
                    ap_poll[0].contents[5].contents[1].text,
                )
            except:  # noqa
                return "UNK", "UNK"

        self.team_name: str = team_name.replace(" ", "-").replace("&", "")
        self.url: str = f"http://www.winsipedia.com/{self.team_name}"

        re: requests.Response = requests.get(url=self.url, headers=HEADERS)
        soup: BeautifulSoup = BeautifulSoup(re.content, features="html.parser")

        self.all_time_record = all_time_record()[0]
        self.all_time_record_rank = all_time_record()[1]
        self.championships = championships()[0]
        self.championships_rank = championships()[1]
        self.conf_championships = conf_championships()[0]
        self.conf_championships_rank = conf_championships()[1]
        self.bowl_games = bowl_games()[0]
        self.bowl_games_rank = bowl_games()[1]
        self.all_time_wins = all_time_wins()[0]
        self.all_time_wins_rank = all_time_wins()[1]
        self.bowl_record = bowl_record()[0]
        self.bowl_record_rank = bowl_record()[1]
        self.consensus_all_americans = consensus_all_americans()[0]
        self.consensus_all_americans_rank = consensus_all_americans()[1]
        self.heisman_winners = heisman_winners()[0]
        self.heisman_winners_rank = heisman_winners()[1]
        self.nfl_draft_picks = nfl_draft_picks()[0]
        self.nfl_draft_picks_rank = nfl_draft_picks()[1]
        self.week_in_ap_poll = weeks_ap_poll()[0]
        self.week_in_ap_poll_rank = weeks_ap_poll()[1]


class CompareWinsipediaTeam:
    __slots__ = [
        "largest_mov",
        "largest_mov_date",
        "longest_win_streak",
        "longest_win_streak_date",
        "name",
    ]

    def __init__(
        self,
        name,
        largest_mov,
        largest_mov_date,
        longest_win_streak,
        largest_win_streak_date,
    ):
        self.largest_mov = largest_mov
        self.largest_mov_date = largest_mov_date
        self.longest_win_streak = longest_win_streak
        self.longest_win_streak_date = largest_win_streak_date
        self.name = name


class CompareWinsipedia:
    __slots__ = ["url", "full_games_url", "all_time_record", "compare", "against"]

    def __init__(self, compare: str, against: str) -> None:
        self.url: str = (
            f"http://www.winsipedia.com/{compare.lower()}/vs/{against.lower()}"
        )
        self.full_games_url: str = (
            f"http://www.winsipedia.com/games/{compare.lower()}/vs/{against.lower()}"
        )

        def mov(which: int) -> list[str]:
            raw_mov: Union[ResultSet, str] = soup.find_all(
                attrs={"class": f"ranking span2 item{which}"}
            )
            raw_mov = raw_mov[0].contents[3].text.replace("\n \n", ":").strip()
            return raw_mov.split(":")

        def win(which: int) -> list[str]:
            raw_win: Union[ResultSet, str] = soup.find_all(
                attrs={"class": f"ranking span2 item{which}"}
            )
            raw_win = raw_win[0].contents[3].text.replace("\n \n", ":").strip()
            return raw_win.split(":")

        def all_time_wins() -> str:
            wins: ResultSet = (
                soup.find_all(attrs={"class": "titleItem left"})[0].contents[1].text
            )
            ties = (
                soup.find_all(attrs={"class": "titleItem center"})[0].contents[1].text
            )
            losses = (
                soup.find_all(attrs={"class": "titleItem right"})[0].contents[1].text
            )

            return f"{wins} wins - {ties} ties - {losses} losses"

        assert (
            compare.replace(" ", "").isalpha() and against.replace(" ", "").isalpha()
        ), StatsException("Team names must only contain alphabet letters.")

        re: requests.Response = requests.get(url=self.url, headers=HEADERS)
        soup: BeautifulSoup = BeautifulSoup(re.content, features="html.parser")

        assert not re.status_code == 404, StatsException(
            f"Unable to find provided teams: {compare}, {against}"
        )

        margin_of_victory: list[str] = mov(1)
        win_stream: list[str] = win(2)
        self.all_time_record: str = all_time_wins()
        self.compare: CompareWinsipediaTeam = CompareWinsipediaTeam(
            name=compare,
            largest_mov=margin_of_victory[0],
            largest_mov_date=margin_of_victory[1],
            longest_win_streak=win_stream[0],
            largest_win_streak_date=win_stream[1],
        )

        margin_of_victory: list[str] = mov(6)
        win_stream: list[str] = win(5)
        self.against: CompareWinsipediaTeam = CompareWinsipediaTeam(
            name=compare,
            largest_mov=margin_of_victory[0],
            largest_mov_date=margin_of_victory[1],
            longest_win_streak=win_stream[0],
            largest_win_streak_date=win_stream[1],
        )


logger.info(f"{str(__name__).title()} module loaded!")
