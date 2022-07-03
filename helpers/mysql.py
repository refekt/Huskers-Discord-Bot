import enum
import inspect
import logging
from typing import Union, Optional

import pymysql
from pymysql import OperationalError

from helpers.constants import SQL_HOST, SQL_USER, SQL_PASSWD, SQL_DB, DEBUGGING_CODE
from helpers.misc import getModuleMethod
from objects.Exceptions import MySQLException
from objects.Logger import discordLogger

if DEBUGGING_CODE:
    logger = discordLogger(name=__name__, level=logging.DEBUG)
else:
    logger = discordLogger(name=__name__, level=logging.INFO)

# Image Command
sqlCreateImageCommand = (
    "INSERT INTO img_cmd_db (author, img_name, img_url) VALUES (% s, % s, % s)"
)

sqlSelectImageCommand = (
    "SELECT author, img_name, img_url FROM img_cmd_db WHERE img_name = % s"
)

sqlSelectAllImageCommand = (
    "SELECT author, img_name, img_url, created_at FROM img_cmd_db"
)

sqlDeleteImageCommand = "DELETE FROM img_cmd_db WHERE img_name = % s AND author = % s"

# Betting
sqlGetTeamInfoByID = "SELECT id, espn_id, school, alt_name, alt_name2, conference, division, color, alt_color, logos1, logos2, location_name, location_city, location_state, location_capacity, location_grass FROM team_ids WHERE id = % s"

sqlGetTeamInfoByESPNID = "SELECT id, espn_id, school, alt_name, alt_name2, conference, division, color, alt_color, logos1, logos2, location_name, location_city, location_state, location_capacity, location_grass FROM team_ids WHERE espn_id = % s"

sqlInsertGameBet = "INSERT INTO bets ( id, author, author_str, created, created_str, opponent, home_game, week, game_datetime, game_datetime_passed, which_team_wins, which_team_overunder, which_team_spread, resolved ) VALUES ( 0, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s )"

sqlUpdateGameBet = "UPDATE bets SET which_team_wins = % s, which_team_overunder = % s, which_team_spread = % s, created = % s, created_str = % s WHERE id = %s"

sqlSelectGameBetbyAuthor = "SELECT id, author, author_str, created, created_str, opponent, week, game_datetime, game_datetime_passed, which_team_wins, which_team_overunder, which_team_spread, resolved FROM bets WHERE author_str = % s AND opponent = % s"

sqlSelectGameBetbyOpponent = "SELECT id, author, author_str, created, created_str, opponent, week, game_datetime, game_datetime_passed, which_team_wins, which_team_overunder, which_team_spread, resolved FROM bets WHERE opponent = % s"

# Croot Bot
sqlTeamIDs = "SELECT id, school FROM team_ids"

sqlGetPrediction = (
    "SELECT * FROM fap_predictions WHERE user_id = % s AND recruit_profile = % s"
)

sqlInsertPrediction = "INSERT INTO fap_predictions ( id, `user`, user_id, recruit_name, recruit_profile, recruit_class, team, confidence, prediction_date, correct, decision_date, committed_team ) VALUES ( % s, % s, % s, % s, % s, % s, % s, % s, % s, NULL, NULL, NULL ) ON DUPLICATE KEY UPDATE ( team = % s, confidence = % s, prediction_date = % s )"

# Back up
# sqlInsertPrediction = "INSERT INTO fap_predictions ( USER, user_id, recruit_name, recruit_profile, recruit_class, team, confidence, prediction_date ) VALUES (% s, % s, % s, % s, % s, % s, % s, Now())"

sqlUpdatePrediction = "UPDATE fap_predictions SET team = % s, confidence = % s, prediction_date = Now() WHERE user_id = % s AND recruit_profile = % s"

# Way to go psys
sqlGetCrootPredictions = "SELECT f.recruit_name, f.team, Avg(f.confidence) AS 'confidence', ( Count(f.team) / t.SUM ) * 100 AS 'percent', t.SUM AS 'total' FROM fap_predictions AS f join ( SELECT recruit_profile, Count(recruit_profile) AS SUM FROM fap_predictions GROUP BY recruit_profile ) AS t ON t.recruit_profile = f.recruit_profile WHERE f.recruit_profile = % s GROUP BY f.recruit_profile, f.recruit_name, f.team ORDER BY percent DESC"

sqlGetIndividualPrediction = "SELECT * FROM fap_predictions WHERE recruit_profile = % s ORDER BY prediction_date ASC"

# Iowa Command
sqlInsertIowa = (
    "INSERT INTO iowa (user_id, reason, previous_roles) VALUES (% s, % s, % s)"
)

sqlRetrieveIowa = "SELECT previous_roles FROM iowa WHERE user_id = % s"

sqlRemoveIowa = "DELETE FROM iowa WHERE user_id = % s"

# Tasks
sqlRetrieveReminders = (
    "SELECT * FROM tasks_repo WHERE is_open = 1 ORDER BY send_when ASC"
)

sqlRecordReminder = "INSERT INTO tasks_repo ( send_to, message, send_when, is_open, author ) VALUES (% s, % s, % s, % s, % s)"

sqlUpdateReminder = "UPDATE tasks_repo SET is_open = % s WHERE send_to = % s AND message = % s AND author = % s"


class SqlFetch(str, enum.Enum):
    all = "all"
    many = "many"
    one = "one"


class SqlQuery:
    __slots__ = [
        "exploded",
        "fetch",
        "processed_query",
        "query",
        "values",
    ]

    def __init__(
        self,
        query: str,
        values: Union[None, str, tuple[str, ...]] = None,
        fetch: Optional[str] = None,
    ) -> None:
        self.query: str = (
            query  # SQL must be "SQL Minify" from https://codebeautify.org/sqlformatter
        )
        self.values: Optional[tuple[str]] = values
        self.fetch: Optional[str] = fetch

        if values is None:
            self.processed_query = self.query
        elif isinstance(values, str):
            self.processed_query = self.query.replace("% s", str(values), 1)
        else:
            l_count = len(values)
            s_count = query.count("% s")
            if s_count == 0:
                self.processed_query = self.query
                return

            if l_count != s_count:
                raise MySQLException(
                    f"Not enough values provided. {l_count} provided bu {s_count} expected."
                )

            self.processed_query = self.query
            for value in self.values:
                self.processed_query = self.processed_query.replace(
                    "% s", str(value), 1
                )
        self.exploded: list[str] = self.processed_query.replace(",", "").split(" ")

    def __str__(self) -> str:
        return self.processed_query

    def __repr__(self) -> str:
        return self.processed_query


def processMySQL(query: str, **kwargs) -> Union[dict, list[dict], None]:
    module, method = getModuleMethod(inspect.stack())

    sql = SqlQuery(
        query=query, values=kwargs.get("values", None), fetch=kwargs.get("fetch", None)
    )

    logger.debug(
        f"Starting a MySQL query called from [{module}-{method}] with query\n\n{sql.processed_query}\n"
    )

    sqlConnection = None
    try:
        sqlConnection = pymysql.connect(
            host=SQL_HOST,
            user=SQL_USER,
            password=SQL_PASSWD,
            db=SQL_DB,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,  # noqa
        )
        logger.debug(f"Connected to the MySQL Database!")
    except OperationalError:  # Unsure if this is the correct exception
        logger.error(f"Unable to connect to the `{SQL_DB}` database.")

    result: Union[dict, list[dict], None] = None

    # try:
    #     with sqlConnection.cursor() as cursor:
    #         if (
    #             "fetch" not in kwargs.keys()
    #         ):  # Try using this instead: tries = kwargs.get('tries', DEFAULT_TRIES)
    #             if "values" not in kwargs.keys():
    #                 cursor.execute(query=query)
    #             else:
    #                 cursor.execute(query=query, args=kwargs["values"])
    #         else:
    #             if "values" not in kwargs.keys():
    #                 if kwargs["fetch"] == "one":
    #                     cursor.execute(query=query)
    #                     result: dict = cursor.fetchone()
    #                 elif kwargs["fetch"] == "many":
    #                     if "size" not in kwargs.keys():
    #                         logger.error("Fetching many requires a `size` kwargs.")
    #                     cursor.execute(query=query)
    #                     result: list[dict] = cursor.fetchmany(many=kwargs["size"])
    #                 elif kwargs["fetch"] == "all":
    #                     cursor.execute(query=query)
    #                     result: list[dict] = cursor.fetchall()
    #             else:
    #                 if kwargs["fetch"] == "one":
    #                     cursor.execute(query=query, args=kwargs["values"])
    #                     result: dict = cursor.fetchone()
    #                 elif kwargs["fetch"] == "many":
    #                     if "size" not in kwargs.keys():
    #                         logger.error("Fetching many requires a `size` kwargs.")
    #                     cursor.execute(query=query, args=kwargs["values"])
    #                     result: list[dict] = cursor.fetchmany(many=kwargs["size"])
    #                 elif kwargs["fetch"] == "all":
    #                     cursor.execute(query=query, args=kwargs["values"])
    #                     result: list[dict] = cursor.fetchall()

    try:
        with sqlConnection.cursor() as cursor:
            if not sql.fetch:
                if sql.values:
                    cursor.execute(query=sql.query)
                else:
                    cursor.execute(query=sql.query, args=sql.values)
            else:
                if not sql.values:
                    if sql.values == SqlFetch.one:
                        cursor.execute(query=sql.query)
                        result: dict = cursor.fetchone()
                    elif sql.fetch == SqlFetch.many:
                        if "size" not in kwargs.keys():
                            logger.error("Fetching many requires a `size` kwargs.")
                        cursor.execute(query=sql.query)
                        result: list[dict] = cursor.fetchmany(many=kwargs["size"])
                    elif sql.fetch == SqlFetch.all:
                        cursor.execute(query=sql.query)
                        result: list[dict] = cursor.fetchall()
                else:
                    if sql.fetch == SqlFetch.one:
                        cursor.execute(query=sql.query, args=sql.values)
                        result: dict = cursor.fetchone()
                    elif sql.fetch == SqlFetch.many:
                        if "size" not in kwargs.keys():
                            logger.error("Fetching many requires a `size` kwargs.")
                        cursor.execute(query=sql.query, args=sql.values)
                        result: list[dict] = cursor.fetchmany(many=kwargs["size"])
                    elif sql.fetch == SqlFetch.all:
                        cursor.execute(query=sql.query, args=sql.values)
                        result: list[dict] = cursor.fetchall()
        sqlConnection.commit()
    except TypeError as err:
        logger.error("Error occurred opening the MySQL database.")
        raise err
    finally:
        logger.debug(f"Closing connection to the MySQL Database")
        sqlConnection.close()

        if result:
            logger.debug(f"Ending a MySQL query called from [{module}-{method}]")
            return result


logger.info(f"{str(__name__).title()} module loaded!")
