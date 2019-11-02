import pymysql.cursors
import config

sqlConnection = pymysql.connect(host=config.sqlHost, user=config.sqlUser, password=config.sqlPass, db=config.sqlDb, charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
print(f"%%% Connected to the MySQL Database! %%%\n"
      f"%%% User: {sqlConnection.user.decode('utf-8')}\n"
      f"%%% Database: {sqlConnection.db.decode('utf-8')}\n"
      f"%%% Connection Check: {sqlConnection.ping}\n"
      f"%%%")