import csv
import random
import time
# from datetime import datetime

import praw
from discord.ext import commands

from utils.consts import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_PW
from utils.misc import on_prod_server

# eNSD = datetime(year=2020, day=16, month=12)


def is_me(ctx):
    return ctx.message.author.id == 189554873778307073


class RedditCommands(commands.Cog):
    @commands.command(hidden=True)
    @commands.check(is_me)
    async def nsd(self, ctx, recruit: str, source: str = None):
        if source is None:
            return await ctx.send(f"A source is required!")

        def load_recruits():
            r = []
            with open("recruits.csv", newline="") as csvfile:
                recruits_raw = csv.reader(csvfile, delimiter=",")
                for recruit_data in recruits_raw:
                    r.append(
                        dict(
                            id=recruit_data[0],
                            data=dict(
                                year=recruit_data[1],
                                name=recruit_data[2],
                                profile=recruit_data[3],
                                stars=recruit_data[4],
                                position=recruit_data[5],
                                cfb_title=f"{recruit_data[1]} {recruit_data[4]}* {recruit_data[5]} {recruit_data[2]} commits to Nebraska",
                                huskers_title=f"🌽 {recruit_data[2]} is N! 🎈"
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
        recruit = recruit.lower()

        try:
            found = False
            for recruit_row in recruits:

                if recruit_row["id"] == recruit:
                    found = True

                    text = f"247Sports Profile: {recruit_row['data']['profile']}\n" \
                           f"\n" \
                           f"Source: {source}"

                    if on_prod_server():
                        huskers = reddit.subreddit("huskers")
                        huskers.submit(
                            title=recruit_row["data"]["huskers_title"],
                            selftext=text
                        )

                        time.sleep(random.randint(1, 2))

                        cfb = reddit.subreddit("cfb")
                        cfb_post = cfb.submit(
                            title=recruit_row["data"]["cfb_title"],
                            selftext=text
                        )

                        try:
                            cfb_post.flair.select("Recruiting")
                            await ctx.send("Set the flair to Recruiting.")
                        except:
                            await ctx.send("Unable to set flair! Make sure you do it.")
                    else:
                        testsub = reddit.subreddit("rngeezus")
                        testsub.submit(
                            title=recruit_row["data"]["cfb_title"],
                            selftext=text
                        )

                        time.sleep(random.randint(1, 2))

                        testsub = reddit.subreddit("rngeezus")
                        testsub.submit(
                            title=recruit_row["data"]["huskers_title"],
                            selftext=text
                        )

                    return await ctx.send(f"Successfully posted threads about {recruit_row['data']['name']}!")

            if not found:
                return await ctx.send(f"Unable to find the player: {recruit}!")

        except IndexError:
            return await ctx.send(f"Key error looking up: {recruit}!")
        except:
            return await ctx.send(f"No idea... {recruit}")


def setup(bot):
    bot.add_cog(RedditCommands(bot))
