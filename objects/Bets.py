import logging
from datetime import datetime
from pprint import pprint
from typing import Union, Optional

import discord

from helpers.misc import alias_param
from helpers.mysql import processMySQL, sqlGetTeamInfoByID

logger = logging.getLogger(__name__)

__all__ = ["Bet"]

logger.info(f"{str(__name__).title()} module loaded!")


class BetMetrics:
    def __init__(self) -> None:
        self.money_line: list[Optional[int]] = [None]
        self.spread: list[Optional[float]] = [None]
        self.total_points: list[Optional[float]] = [None]


class BetTeam:
    __slots__ = [
        "alt_name",
        "city",
        "conference",
        "division",
        "id_str",
        "logo",
        "school_name",
        "stadium",
        "state",
    ]

    def __init__(self, from_dict: dict = None, *args, **kwargs) -> None:
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
            self.alt_name: Optional[str] = None
            self.city: Optional[str] = None
            self.conference: Optional[str] = None
            self.division: Optional[str] = None
            self.id_str: Optional[str] = None
            self.logo: Optional[str] = None
            self.school_name: Optional[str] = None
            self.stadium: Optional[str] = None
            self.state: Optional[str] = None


def buildTeam(id_str: str) -> BetTeam:
    query = processMySQL(query=sqlGetTeamInfoByID, fetch="one", values=id_str)
    return BetTeam(from_dict=query)


class Bet:
    def __init__(
        self,
        author: Union[discord.Member, discord.User],
    ) -> None:
        self.author: discord.Member = author
        self.author_str: str = f"{self.author.name}#{self.author.discriminator}"
        self.bet_values: BetMetrics = BetMetrics()
        self.created: datetime = datetime.now()
        self.created_str: str = str(self.created)
        self.game_datetime: Optional[datetime] = None
        self.game_datetime_passed: bool = datetime.now() >= self.game_datetime or False
        self.resolved: bool = False
        self.teams: list[BetTeam] = [BetTeam(), BetTeam()]


# Testing

if __name__ == "__main__":
    test = buildTeam("8483250")
    pprint(test)
