import pymysql.cursors

from utilities.constants import SQL_HOST, SQL_PASSWD, SQL_DB, SQL_USER

sqlDatabaseTimestamp = """
INSERT INTO bot_connections (user, connected, timestamp) VALUES (%s, %s, %s)
"""

sqlLogError = """
INSERT INTO bot_error_log (user, error) VALUES (%s, %s)
"""

sqlLogUser = """
INSERT INTO bot_user_log (user, event, comment) VALUES (%s, %s, %s)
"""

sqlLeaderboard = """\
SELECT user, COUNT(*) as num_games_bet_on, SUM(CASE b.win WHEN g.win THEN 1 ELSE 0 END) as correct_wins, SUM(CASE b.spread WHEN g.spread THEN 1 ELSE 0 END) as correct_spreads, SUM(CASE b.moneyline WHEN g.moneyline THEN 1 ELSE 0 END) as correct_moneylines, SUM(CASE b.win WHEN g.win THEN 1 ELSE 0 END + CASE b.spread WHEN g.spread THEN 2 ELSE 0 END + CASE b.moneyline WHEN g.moneyline THEN 2 ELSE 0 END) as total_points FROM bets b INNER JOIN games g ON (b.game_number =  g.game_number) WHERE g.finished = true GROUP BY user ORDER BY total_points DESC;
"""

sqlAdjustedLeaderboard = """\
SELECT user, COUNT(*) as num_games_bet_on, SUM(CASE b.win WHEN g.win THEN 1 ELSE 0 END) as correct_wins, SUM(CASE b.spread WHEN g.spread THEN 1 ELSE 0 END) as correct_spreads, SUM(CASE b.moneyline WHEN g.moneyline THEN 1 ELSE 0 END) as correct_moneylines, SUM(CASE b.win WHEN g.win THEN 1 ELSE 0 END + CASE b.spread WHEN g.spread THEN 2 ELSE 0 END + CASE b.moneyline WHEN g.moneyline THEN 2 ELSE 0 END) / COUNT(*) as avg_pts_per_game FROM bets b INNER JOIN games g ON (b.game_number =  g.game_number) WHERE g.finished = true GROUP BY user ORDER BY avg_pts_per_game DESC;
"""

sqlGetWinWinners = """
SELECT b.user FROM bets b INNER JOIN games g ON (b.game_number =  g.game_number) WHERE b.win = g.win AND g.opponent = %s;
"""

sqlGetSpreadWinners = """
SELECT b.user FROM bets b INNER JOIN games g ON (b.game_number =  g.game_number) WHERE b.spread = g.spread AND g.opponent = %s;
"""

sqlGetMoneylineWinners = """
SELECT b.user FROM bets b INNER JOIN games g ON (b.game_number =  g.game_number) WHERE b.moneyline = g.moneyline AND g.opponent = %s;
"""

sqlInsertWinorlose = """
INSERT INTO bets (game_number, user, win, date_updated) VALUES  (%s, %s, %s, NOW()) ON DUPLICATE KEY UPDATE  win=%s;
"""

sqlInsertSpread = """
INSERT INTO bets (game_number, user, spread, date_updated) VALUES  (%s, %s, %s, NOW()) ON DUPLICATE KEY UPDATE  spread=%s;
"""

sqlInsertMoneyline = """
INSERT INTO bets (game_number, user, moneyline, date_updated) VALUES  (%s, %s, %s, NOW())  ON DUPLICATE KEY UPDATE  moneyline=%s;
"""

sqlRetrieveBet = """
SELECT * FROM bets b WHERE b.user = %s;
"""

sqlRetrieveSpecificBet = """
SELECT * FROM bets b WHERE b.game_number = %s AND b.user = %s;
"""

sqlRetrieveGameNumber = """
SELECT g.game_number FROM games g WHERE g.opponent = %s;
"""

sqlRetrieveAllBet = """
SELECT * FROM bets b WHERE b.game_number = %s;
"""

sqlUpdateScores = """
INSERT INTO games (game_number, score, opponent_score) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE score=%s, opponent_score=%s
"""

sqlUpdateAllBetCategories = """
INSERT INTO games (game_number, finished, win, spread, moneyline) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE finished=%s, win=%s, spread=%s, moneyline=%s
"""

sqlRetrieveGameInfo = """
SELECT * FROM games g WHERE g.game_number = %s;
"""

sqlRetrieveCrystalBallLastRun = """
SELECT last_run FROM cb_lastrun
"""

sqlUpdateCrystalLastRun = """
INSERT INTO cb_lastrun (last_run) VALUES (%s)
"""

sqlUpdateCrystalBall = """
INSERT INTO crystal_balls (first_name, last_name, full_name, photo, prediction, result) VALUES (%s, %s, %s, %s, %s, %s)
"""

sqlRetrieveRedditInfo = """
SELECT * FROM subreddit_info;
"""

sqlUpdateLineInfo = """
INSERT INTO games (game_number, spread_value, moneyline_value) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE spread_value=%s, moneyline_value=%s
"""

sqlRetrieveTriviaQuestions = """
SELECT * FROM trivia
"""

sqlInsertTriviaScore = """
INSERT INTO trivia_scores (user, score) VALUES (%s, %s) ON DUPLICATE KEY UPDATE score=score+%s
"""

sqlZeroTriviaScore = """
INSERT INTO trivia_scores (user, score) VALUES (%s, %s) ON DUPLICATE KEY UPDATE score=score+%s
"""

sqlRetrieveTriviaScores = """
SELECT * FROM trivia_scores ORDER BY score DESC
"""

sqlClearTriviaScore = """
TRUNCATE TABLE trivia_scores
"""

sqlTeamIDs = """
SELECT id, name FROM team_ids ORDER BY name ASC
"""

sqlRecordStats = """
INSERT INTO stats (author, channel) VALUES (%s, %s)
"""

sqlRecordStatsManual = """
INSERT INTO stats (author, channel, created_at) VALUES (%s, %s, %s)
"""

sqlRetrieveStats = """
SELECT * FROM stats
"""

sqlRetrieveTasks = """
SELECT * FROM tasks_repo WHERE is_open = 1
"""

sqlRecordTasks = """
INSERT INTO tasks_repo (send_to, message, send_when, is_open, author) VALUES (%s, %s, %s, %s, %s)
"""

sqlUpdateTasks = """
UPDATE tasks_repo SET is_open = %s WHERE send_to = %s AND message = %s AND send_when = %s AND author = %s
"""

sqlRetrieveCurrencyLeaderboard = """
SELECT * FROM currency ORDER BY balance DESC
"""

sqlRetrieveCurrencyUser = """
SELECT balance FROM currency WHERE user_id = %s
"""

sqlCheckCurrencyInit = """
SELECT init FROM currency WHERE user_id = %s
"""

sqlSetCurrency = """
INSERT INTO currency (username, init, balance, user_id) VALUES (%s, 1, %s, %s)
"""

sqlUpdateCurrency = """
UPDATE currency SET balance = balance + %s WHERE username = %s
"""

sqlInsertIowa = """
INSERT INTO iowa (user_id, reason, previous_roles) VALUES (%s, %s, %s)
"""

sqlRetrieveIowa = """
SELECT previous_roles FROM iowa WHERE user_id = %s
"""

sqlRemoveIowa = """
DELETE FROM iowa WHERE user_id = %s
"""

sqlRetrieveAllCustomLinesKeywords = """
SELECT clb.author, cl.keyword, cl.description, clb.value, clb._for, clb.against, cl.author as orig_author, cl.result FROM custom_lines_bets clb INNER JOIN custom_lines cl ON (cl.keyword = clb.keyword ) WHERE clb.keyword = %s
"""

sqlRetrieveOneCustomLinesKeywords = """
SELECT clb.author, cl.keyword, cl.description, clb.value, clb._for, clb.against, cl.author as orig_author, cl.result FROM custom_lines_bets clb INNER JOIN custom_lines cl ON (cl.keyword = clb.keyword ) WHERE clb.keyword = %s AND clb.author = %s
"""

sqlInsertCustomLines = """
INSERT INTO custom_lines (author, keyword, description, result) VALUES (%s, %s, %s, 'tbd')
"""

sqlRetrieveAllOpenCustomLines = """
SELECT * FROM custom_lines WHERE result = 'tbd'
"""

sqlRetreiveCustomLinesForAgainst = """
SELECT author, _for, against, value FROM custom_lines_bets WHERE keyword = %s
"""

sqlRetrieveOneOpenCustomLine = """
SELECT * FROM custom_lines WHERE keyword = %s and result = 'tbd'
"""

sqlInsertCustomLinesBets = """
INSERT INTO custom_lines_bets (author, keyword, _for, against, value) VALUES (%s, %s, %s, %s, %s)
"""

sqlUpdateCustomLinesBets = """
UPDATE custom_lines_bets SET `_for`=%s, against=%s, value=%s WHERE author=%s AND keyword=%s
"""

sqlUpdateCustomLinesResult = """
UPDATE custom_lines SET result = %s WHERE keyword = %s
"""


def Process_MySQL(query: str, **kwargs):
    try:
        sqlConnection = pymysql.connect(
            host=SQL_HOST,
            user=SQL_USER,
            password=SQL_PASSWD,
            db=SQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        if not query == sqlRecordStats:
            print(f"%%% Connected to the MySQL Database! %%%\n"
                  f"%%% Preparing to execute [`{repr(query)}`{'] and [`' + repr(kwargs) + '`' if kwargs else ''}]")
    except:
        print(f"Unable to connect to the `{SQL_DB}` database.")
        return

    result = None

    try:
        with sqlConnection.cursor() as cursor:
            if not "fetch" in kwargs:  # Try using this instead: tries = kwargs.get('tries', DEFAULT_TRIES)
                if not "values" in kwargs:
                    cursor.execute(query=query)
                else:
                    cursor.execute(query=query, args=kwargs["values"])
            else:
                if not 'values' in kwargs:
                    if kwargs["fetch"] == "one":
                        cursor.execute(query=query)
                        result = cursor.fetchone()
                    elif kwargs["fetch"] == "many":
                        if not "size" in kwargs:
                            raise ValueError("Fetching many requires a `size` kwargs.")
                        cursor.execute(query=query)
                        result = cursor.fetchmany(many=kwargs["size"])
                    elif kwargs["fetch"] == "all":
                        cursor.execute(query=query)
                        result = cursor.fetchall()
                else:
                    if kwargs["fetch"] == "one":
                        cursor.execute(query=query, args=kwargs['values'])
                        result = cursor.fetchone()
                    elif kwargs["fetch"] == "many":
                        if not "size" in kwargs:
                            raise ValueError("Fetching many requires a `size` kwargs.")
                        cursor.execute(query=query, args=kwargs['values'])
                        result = cursor.fetchmany(many=kwargs["size"])
                    elif kwargs["fetch"] == "all":
                        cursor.execute(query=query, args=kwargs['values'])
                        result = cursor.fetchall()

        sqlConnection.commit()

    except:
        raise ConnectionError("Error occurred opening the MySQL database.")
    finally:
        if not query == sqlRecordStats:
            print(f"%%% Closing connection to the MySQL Database! %%%")
        sqlConnection.close()

        if result:
            return result
