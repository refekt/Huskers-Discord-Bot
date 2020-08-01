import random
import time
from datetime import datetime

import praw
from discord.ext import commands

from utils.client import client
from utils.consts import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_PW

eNSD = datetime(year=2019, day=18, month=12)


def is_me(ctx):
    return ctx.message.author.id == 189554873778307073


class RedditCommands(commands.Cog):
    @commands.command(hidden=True)
    @commands.check(is_me)
    async def nsd(self, ctx, recruit: str, source: str = None):
        if source is None:
            await ctx.send(f"A source is required!")
            return

        def load_recruits():
            import csv
            r = []
            with open("recruits.csv", newline="") as csvfile:
                recruits_raws = csv.reader(csvfile, delimiter=",")
                for row in recruits_raws:
                    r.append(
                        dict(
                            id=row[0],
                            data=dict(
                                year=row[1],
                                name=row[2],
                                profile=row[3],
                                stars=row[4],
                                position=row[5],
                                cfb_title=f"{row[1]} {row[4]}* {row[5]} {row[2]} commits to Nebraska",
                                huskers_title=f"🌽 {row[2]} is N! 🎈"
                            )
                        )
                    )
            del r[0]

            return r

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent="Scotty McFrosty",
            username="refekt",
            password=REDDIT_PW
        )

        recruits = load_recruits()

        me = client.get_user(189554873778307073)
        recruit = recruit.lower()

        try:
            found = False
            for recruit_row in recruits:

                if recruit_row["id"] == recruit:
                    found = True

                    text = f"247Sports Profile: {recruit_row['data']['profile']}\n" \
                           f"\n" \
                           f"Source: {source}"

                    from utils.misc import on_prod_server

                    if on_prod_server():
                        huskers = reddit.subreddit("huskers")
                        huskers.submit(
                            title=recruit_row["data"]["huskers_title"],
                            selftext=text
                        )

                        time.sleep(random.randint(1, 3))

                        cfb = reddit.subreddit("cfb")
                        cfb_post = cfb.submit(
                            title=recruit_row["data"]["cfb_title"],
                            selftext=text
                        )

                        try:
                            cfb_post.flair.select("Recruiting")
                        except:
                            await ctx.send("Unable to set flair! Make sure you do it.")
                            pass

                    elif not on_prod_server():
                        testsub = reddit.subreddit("rngeezus")
                        testsub.submit(
                            title=recruit_row["data"]["cfb_title"],
                            selftext=text
                        )

                        time.sleep(random.randint(1, 3))

                        testsub = reddit.subreddit("rngeezus")
                        testsub.submit(
                            title=recruit_row["data"]["huskers_title"],
                            selftext=text
                        )

                    await ctx.send(f"Successfully posted threads about {recruit_row['data']['name']}!")

                    break

            if not found:
                await ctx.send(f"Unable to find the player: {recruit}!")
                return

        except IndexError:
            await ctx.send(f"Key error looking up: {recruit}!")
            return
        except:
            await ctx.send(f"No idea... {recruit}")
            return


def setup(bot):
    bot.add_cog(RedditCommands(bot))
