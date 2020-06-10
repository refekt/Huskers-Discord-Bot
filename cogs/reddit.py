import random
import time
from datetime import datetime

import praw
from discord.ext import commands

from utils.client import client
from utils.consts import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_PW

recruits = {
    "neville": ["Latrell Neville", "3*", "WR", "https://247sports.com/Player/Latrell-Neville-46054704/", "Neville is N!", "2021 3* WR Latrell Neville commits to Nebraska"],
    "will": ["Will Schweitzer", "3*", "OLB", "https://247sports.com/Player/Will-Schweitzer-46081968/", "Schweitzer is N!", "2021 3* OLB Will Schweitzer commits to Nebraska"],
    "fidone": ["Thomas Fidone", "4*", "TE", "https://247sports.com/Player/Thomas-Fidone-46086515/", "Fidone is N!", "2021 3* TE Thomas Fidone commits to Nebraska"]
}

eNSD = datetime(year=2019, day=18, month=12)


def is_me(ctx):
    return ctx.message.author.id == 189554873778307073


class RedditCommands(commands.Cog):
    @commands.command(hidden=True)
    @commands.check(is_me)
    async def nsd(self, ctx, recruit: str, source: str = ""):
        me = client.get_user(189554873778307073)

        try:
            recruit = recruit.lower()
            if not recruit in recruits:
                await me.send(f"Unable to find {recruit}")
                return
        except IndexError:
            await me.send(f"Key error on {recruit}")
            return
        except:
            await me.send(f"No idea...{recruit}")
            return

        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_SECRET,
            user_agent="Scotty McFrosty",
            username="refekt",
            password=REDDIT_PW
        )

        # 0 == name, 1 == stars, 2 == position, 3 == url, 4 == /r/huskers, 5 == /r/cfb
        text = f"247Sports Profile: {recruits[recruit][3]}\n" \
               f"\n" \
               f"Source: {source}"

        # Testing sub reddit
        # huskers = reddit.subreddit("ThisIsDarkSouls")
        # huskers.submit(
        #     title=recruits[recruit][4],
        #     selftext=text
        # )

        huskers = reddit.subreddit("huskers")
        huskers.submit(
            title=recruits[recruit][4],
            selftext=text
        )

        time.sleep(random.randint(1, 4))

        cfb = reddit.subreddit("cfb")
        cfb_post = cfb.submit(
            title=recruits[recruit][5],
            selftext=text
        )

        try:
            cfb_post.falir.select("Recruiting")
        except:
            await ctx.send("Unable to set flair! Make sure you do it.")
            pass


def setup(bot):
    bot.add_cog(RedditCommands(bot))
