import schedule, time
from cogs.croot_bot import check_last_run


async def job():
    print("Woo")
    await check_last_run()


async def main():
    # schedule.every(4).hour.do(job)
    print("scheduling")
    await schedule.every(15).seconds.do(job)
    print("scheduled")
    print("about to loop")
    while True:
        print("looping")
        await schedule.run_pending()
        time.sleep(1)