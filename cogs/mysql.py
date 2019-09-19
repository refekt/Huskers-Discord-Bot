import pymysql.cursors

connection = pymysql.connect(host='vps.j3y.org',
                             user='huskerbot',
                             password='ThroughTheseGates1!',
                             db='huskerbot',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

try:
    with connection.cursor() as cursor:
        # Create a new record
        sql = "INSERT INTO bets (game_number, user, win, spread, moneyline) VALUES (1, 'user#1234', true, true, true);"
        cursor.execute(sql)

    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()
    #
    # with connection.cursor() as cursor:
    #     # Read a single record
    #     sql = "SELECT `game_number`, `user`, `moneyline`, `win`, `spread` FROM `bets` WHERE *"
    #     cursor.execute(sql, ('webmaster@python.org',))
    #     result = cursor.fetchone()
    #     print(result)
finally:
    connection.close()