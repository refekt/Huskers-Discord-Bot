import pymysql.cursors
import config

sqlConnection = pymysql.connect(host=config.sqlHost, user=config.sqlUser, password=config.sqlPass, db=config.sqlDb, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
print("%%% Connected to the MySQL Database! %%%\n"
      "%%% User: {}\n"
      "%%% Connection Check: {}\n%%%".format(sqlConnection.user, sqlConnection.ping))