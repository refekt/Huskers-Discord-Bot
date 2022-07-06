import datetime
import time

import schedule

time_str: str = "15:40"

schedule.every().monday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().tuesday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().wednesday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().thursday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().friday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().saturday.at(time_str).do(print, f"{datetime.datetime.now()} testing")
schedule.every().sunday.at(time_str).do(print, f"{datetime.datetime.now()} testing")

all_jobs = schedule.jobs

[print(job) for job in all_jobs]

while True:
    schedule.run_pending()
    time.sleep(1)
