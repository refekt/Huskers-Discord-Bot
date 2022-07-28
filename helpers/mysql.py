import enum
import inspect
import logging
from typing import Union, Optional, Any

import pymysql
from pymysql import OperationalError, Connection, IntegrityError, ProgrammingError

from helpers.constants import SQL_HOST, SQL_USER, SQL_PASSWD, SQL_DB, DEBUGGING_CODE
from helpers.misc import getModuleMethod
from objects.Exceptions import MySQLException
from objects.Logger import discordLogger

logger = discordLogger(
    name=__name__, level=logging.DEBUG if DEBUGGING_CODE else logging.INFO
)

__all__: list[str] = [
    "SqlFetch",
    "processMySQL",
    "sqlCreateImageCommand",
    "sqlDeleteImageCommand",
    "sqlGetBetsLeaderboard",
    "sqlGetCrootPredictions",
    "sqlGetIndividualPrediction",
    "sqlGetPrediction",
    "sqlGetTeamInfoByESPNID",
    "sqlGetTeamInfoByID",
    "sqlGetWordleIndividualUserScore",
    "sqlGetWordleScores",
    "sqlInsertGameBet",
    "sqlInsertIowa",
    "sqlInsertPrediction",
    "sqlInsertWordle",
    "sqlRecordReminder",
    "sqlRemoveIowa",
    "sqlResolveGame",
    "sqlRetrieveIowa",
    "sqlRetrieveReminders",
    "sqlSelectAllImageCommand",
    "sqlSelectGameBetbyAuthor",
    "sqlSelectGameBetbyOpponent",
    "sqlSelectImageCommand",
    "sqlTeamIDs",
    "sqlUpdateGameBet",
    "sqlUpdatePrediction",
    "sqlUpdateReminder",
]

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

sqlInsertGameBet = "INSERT INTO bets ( id, author, author_str, created, created_str, opponent, home_game, week, game_datetime, game_datetime_passed, predict_game, predict_points, predict_spread, resolved ) VALUES ( 0, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s )"

sqlUpdateGameBet = "UPDATE bets SET predict_game = % s, predict_points = % s, predict_spread = % s, created = % s, created_str = % s WHERE id = %s"

sqlSelectGameBetbyAuthor = "SELECT id, author, author_str, created, created_str, opponent, week, game_datetime, game_datetime_passed, predict_game, predict_points, predict_spread, resolved FROM bets WHERE author_str = % s AND opponent = % s"

sqlSelectGameBetbyOpponent = "SELECT id, author, author_str, created, created_str, opponent, week, game_datetime, game_datetime_passed, predict_game, predict_points, predict_spread, resolved FROM bets WHERE opponent = % s"

sqlGetBetsLeaderboard = "SELECT * FROM `bets_leaderboard.v`"

sqlResolveGame = "UPDATE botfrost.schedule_22 SET game_datetime_passed = 1, result_game = % s, result_points = % s, result_spread = % s, resolved = 1 WHERE opponent = % s;"

# Croot Bot
sqlTeamIDs = "SELECT id, school FROM team_ids"

sqlGetPrediction = (
    "SELECT * FROM fap_predictions WHERE user_id = % s AND recruit_profile = % s"
)

sqlInsertPrediction = "INSERT INTO fap_predictions ( id, `user`, user_id, recruit_name, recruit_profile, recruit_class, team, confidence, prediction_date, correct, decision_date, committed_team ) VALUES ( % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s, % s ) ON DUPLICATE KEY UPDATE ( team = % s, confidence = % s, prediction_date = % s )"

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

# Wordle

sqlInsertWordle = "INSERT INTO wordle (id, author, which_day, score, green_squares, yellow_squares, black_squares) VALUES (% s, % s, % s, % s, % s, % s, % s)"  # ON DUPLICATE KEY UPDATE ( score = % s, green_squares = % s, yellow_squares = % s, black_squares = % s)"
sqlGetWordleScores = "SELECT author, games_played, score_avg, green_avg, yellow_avg, black_avg FROM `wordle.v`"
sqlGetWordleScoresv2 = "SELECT *, Dense_rank() OVER ( ORDER BY games_played DESC ) AS 'lb_rank' FROM `wordle.v` wv"
sqlGetWordleIndividualUserScore = "SELECT *, Dense_rank() OVER ( ORDER BY score_avg asc ) AS 'lb_rank' FROM `wordle.v` wv"


class SqlFetch(str, enum.Enum):
    all = "all"
    many = "many"
    one = "one"


class SqlQuery:
    __slots__ = [
        "fetch",
        "query",
        "values",
    ]

    def __init__(
        self,
        query: str,
        values: Union[None, str, tuple[str, ...]] = None,
        fetch: Optional[str] = None,
    ) -> None:
        self.fetch: Optional[str] = fetch
        self.query: str = (
            query  # SQL must be "SQL Minify" from https://codebeautify.org/sqlformatter
        )
        self.values: Optional[tuple[str]] = values

    @property
    def processed_query(self) -> str:
        if self.values is None:
            return self.query
        elif isinstance(self.values, str):
            return self.query.replace(
                "% s",
                f"'{self.values}'" if type(self.values) == str else str(self.values),
                1,
            )
        else:
            values_count = len(self.values)
            sql_s_count = self.query.count("% s")

            if sql_s_count == 0:
                return self.query

            if values_count != sql_s_count:
                raise MySQLException(
                    f"Not enough self.values provided. {values_count} provided bu {sql_s_count} expected."
                )

            _temp_query: str = self.query
            for value in self.values:
                _temp_query = self.processed_query.replace(
                    "% s", f"'{value}'" if type(value) == str else str(value), 1
                )

            return _temp_query

    @property
    def exploded(self) -> list[str]:
        return (
            self.processed_query.replace(",", "")
            .replace("(", "")
            .replace(")", "")
            .split(" ")
        )

    def __str__(self) -> str:
        return self.processed_query

    def __repr__(self) -> str:
        return self.processed_query


def processMySQL(
    query: str, **kwargs
) -> Union[dict, list[dict, ...], tuple[tuple[Any, ...], ...], None]:
    module, method = getModuleMethod(inspect.stack())

    sql_qeury: SqlQuery = SqlQuery(
        fetch=kwargs.get("fetch", None),
        query=query,
        values=kwargs.get("values", None),
    )

    # TODO Fix processed_Query
    # logger.debug(
    #     f"Starting a MySQL query called from [{module}-{method}] with query\n\n{sql_qeury.processed_query}\n"
    # )
    logger.debug(f"Starting a MySQL query called from [{module}-{method}] with query\n")

    sqlConnection: Optional[Connection] = None
    try:
        sqlConnection = pymysql.connect(
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,  # noqa
            db=SQL_DB,
            host=SQL_HOST,
            password=SQL_PASSWD,
            user=SQL_USER,
        )
        logger.debug(f"Connected to the MySQL Database!")
    except OperationalError:  # Unsure if this is the correct exception
        logger.exception(f"Unable to connect to the `{SQL_DB}` database.")

    result: Union[dict, list[dict, ...], tuple[tuple[Any, ...], ...], None] = None

    try:
        with sqlConnection.cursor() as cursor:
            cursor.execute(query=sql_qeury.query, args=sql_qeury.values)

            if sql_qeury.fetch:
                if sql_qeury.fetch == SqlFetch.one:
                    result = cursor.fetchone()
                elif sql_qeury.fetch == SqlFetch.many:
                    if "size" not in kwargs.keys():
                        logger.exception("Fetching many requires a `size` kwargs.")
                    result = cursor.fetchmany(size=kwargs["size"])
                elif sql_qeury.fetch == SqlFetch.all:
                    result = cursor.fetchall()

        sqlConnection.commit()
    except IntegrityError as err:
        logger.exception("Error occurred opening the MySQL database.")
        raise MySQLException(f"Integrity Error: {err.args[1]}")
    except ProgrammingError as err:
        logger.warning("Error occurred opening the MySQL database.")
        raise MySQLException(f"MySQL Syntax error: {err.args[1]}")
    finally:
        logger.debug(f"Closing connection to the MySQL Database")
        sqlConnection.close()

        if result:
            logger.debug(f"Ending a MySQL query called from [{module}-{method}]")
            return result


logger.info(f"{str(__name__).title()} module loaded!")
