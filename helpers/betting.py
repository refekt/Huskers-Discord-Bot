import logging
from datetime import datetime
from typing import Union

from cfbd import Configuration, BettingApi, ApiClient, GamesApi
from cfbd.rest import ApiException

from helpers.constants import CFBD_KEY
from objects.Exceptions import BettingException

logger = logging.getLogger(__name__)

logger.info(f"{str(__name__).title()} module loaded!")

__all__ = [
    "get_consensus_line",
    "get_current_week",
]


cfbd_config = Configuration()
cfbd_config.api_key["Authorization"] = CFBD_KEY
cfbd_config.api_key_prefix["Authorization"] = "Bearer"


def get_consensus_line(
    team_name: str, year: int = datetime.now().year, week: int = None
) -> Union[None, str]:
    logger.info(f"Getting the concensus line for {year} Week {week} {team_name} game")

    cfb_api = BettingApi(ApiClient(cfbd_config))

    if week is None:
        week = get_current_week(year=year, team=team_name)

    try:
        api_response = cfb_api.get_lines(team=team_name, year=year, week=week)
    except (ApiException, TypeError):
        return None

    logger.info(f"Results: {api_response}")

    try:
        lines = None  # Hard code Week 0

        for game in api_response:
            if game.away_score is None and game.home_score is None:
                lines = game.lines[0]
                break

        logger.info(f"Lines: {lines}")

        formattedSpread = (
            lines.get("formattedSpread") if lines.get("formattedSpread", None) else ""
        )
        spreadOpen = lines.get("spreadOpen") if lines.get("spreadOpen", None) else "N/A"
        overUnder = lines.get("overUnder") if lines.get("overUnder", None) else ""
        overUnderOpen = (
            lines.get("overUnderOpen") if lines.get("overUnderOpen", None) else "N/A"
        )
        homeMoneyline = (
            str(lines.get("homeMoneyline")) if lines.get("homeMoneyline", None) else ""
        )
        awayMoneyline = (
            str(lines.get("awayMoneyline")) if lines.get("awayMoneyline", None) else ""
        )

        new_line = "\n"
        consensus_line = (
            f"{'Spread: ' + formattedSpread + ' (Opened: ' + spreadOpen + ')' + new_line}"
            f"{'Over/Under:  ' + overUnder + ' (Opened: ' + overUnderOpen + ')' + new_line}"
            f"{'Home Moneyline: ' + homeMoneyline + new_line}"
            f"{'Away Moneyline: ' + awayMoneyline + new_line }"
        )

    except IndexError:
        return None

    return consensus_line


def get_current_week(year: int, team: str) -> int:
    logger.info(f"Getting the current week for the {year} {team} game")
    api = GamesApi(ApiClient(cfbd_config))

    try:
        games = api.get_games(
            year=year, team="nebraska"
        )  # We only care about Nebraska's schedule
    except ApiException:
        logger.exception("CFBD API unable to get games", exc_info=True)
        raise BettingException("CFBD API unable to get games")

    for index, game in enumerate(games):
        logger.info(f"Checking the Week {game.week} game.")
        if team.lower() == "nebraska":
            if game.week == games[1].week:  # Week 0 game
                return 0

            if not (game.away_points and game.home_points):
                return game.week
            else:
                logger.exception(
                    "Unknown error ocurred when getting week for Nebraska game",
                    exc_info=True,
                )
        elif (
            game.away_team.lower() == "nebraska" or game.home_team.lower() == "nebraska"
        ) and (
            game.away_team.lower() == team.lower()
            or game.home_team.lower() == team.lower()
        ):
            return game.week

    logger.exception(f"Unable to find week for {team}")
    raise BettingException(f"Unable to find week for {team}")
