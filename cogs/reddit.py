import random
import time
from datetime import datetime

import praw
from discord.ext import commands

from utils.client import client
from utils.consts import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_PW

recruits = {
    "neville": ["Latrell Neville", "3*", "WR", "https://247sports.com/Player/Latrell-Neville-46054704/", "Neville is N!", "2021 3* WR Latrell Neville commits to Nebraska"],
    "fidone": ["Thomas Fidone", "4*", "TE", "https://247sports.com/Player/Thomas-Fidone-46086515/", "Fidone is N!", "2021 3* TE Thomas Fidone commits to Nebraska"],
    "bryant": ["Sirad Bryant", "3*", "S", "https://247sports.com/player/sirad-bryant-46094973/", "Bryant is N!", "2021 3* S Sirad Bryant commits to Nebraska"],
    "van": ["Geno VanDeMark", "4*", "OG", "https://247sports.com/player/geno-vandemark-46081733/", "VanDeMark is N!", "2021 4* OG Geno VanDeMark commits to Nebraska"],
    "burkhalter": ["Christian Burkhalter", "3*", "WDE", "https://247sports.com/player/christian-burkhalter-46056902/", "Burkhalter is N!", "2021 3* WDE Christian Burkhalter commits to Nebraska"],
    "buckley": ["Ru'Quan Buckley", "3*", "OT", "https://247sports.com/player/ruquan-buckley-46082019/", "Buckley is N!", "2021 3* OT Ru'Quan Buckley commits to Nebraska"],
    "okoli": ["Tobechi Okoli", "3*", "SDE", "https://247sports.com/player/tobechi-okoli-46094840/", "Okoli is N!", "2021 3* SDE Tobechi Okoli commits to Nebraska"],
    "berry": ["Caleb Berry", "3*", "RB", "https://247sports.com/player/caleb-berry-46080989/", "Berry is N!", "2021 3* RB Caleb Berry commits to Nebraska"]
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

        from utils.misc import on_prod_server

        if on_prod_server():
            huskers = reddit.subreddit("huskers")
            huskers.submit(
                title=recruits[recruit][4],
                selftext=text
            )

            time.sleep(random.randint(1, 3))

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
        elif not on_prod_server():
            testsub = reddit.subreddit("rngeezus")
            testsub.submit(
                title=recruits[recruit][4],
                selftext=text
            )

            time.sleep(random.randint(1, 3))

            testsub = reddit.subreddit("rngeezus")
            testsub.submit(
                title=recruits[recruit][5],
                selftext=text
            )

        await ctx.send(f"Successfully posted threads about {recruits[recruit][0]}!")


def setup(bot):
    bot.add_cog(RedditCommands(bot))
