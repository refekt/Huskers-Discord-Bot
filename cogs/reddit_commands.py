from discord.ext import commands
import discord
import mysql
import config
import requests
import requests.auth
import json

globalRate = 3
globalPer = 30
max_posts = 5

user_agent = "Frosty by refekt"


def reddit_oath():
    with mysql.sqlConnection.cursor() as cursor:
        cursor.execute(config.sqlRetrieveRedditInfo)
        reddit_info = cursor.fetchall()
    mysql.sqlConnection.commit()
    cursor.close()

    client_auth = requests.auth.HTTPBasicAuth(reddit_info[0]["client_id"], reddit_info[0]["client_secret"])
    post_data = {"grant_type": "password", "username": reddit_info[0]["username"], "password": reddit_info[0]["password"]}
    headers = {"User-Agent": user_agent}

    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    token_info = response.json()

    return token_info


class RedditCommands(commands.Cog, name="Reddit Commands"):
    @commands.group()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def sub(self, ctx):
        """Interacts with the r/Huskers subreddit"""
        pass

    @sub.command()
    async def recent(self, ctx, count=5):
        """Outputs the most recent submissions on r/Huskers. Default is 5."""
        token_info = reddit_oath()
        headers = {"Authorization": "bearer {}".format(token_info["access_token"]), "User-Agent": user_agent}
        response = requests.get("https://oauth.reddit.com/r/huskers/new", headers=headers)
        posts = response.json()

        dump = False
        if dump:
            with open("huskers_sub.json", "w") as fp:
                json.dump(posts, fp, sort_keys=True, indent=4)
            fp.close()

        for index, post in enumerate(posts["data"]["children"]):
            if index == count:
                break

            post_title = post["data"]["title"]
            post_author = post["data"]["author"]
            post_ups = post["data"]["ups"]
            post_downs = post["data"]["downs"]
            post_permalink = "https://reddit.com{}".format(post["data"]["permalink"])
            if post["data"]["thumbnail"] == "self":
                post_thumbnail = "https://i.imgur.com/Ah3x5NA.png"
            else:
                post_thumbnail = post["data"]["thumbnail"]

            embed = discord.Embed(title="⬆ {} ⬇ {} - {}".format(post_ups, post_downs, post_title), color=0xFF0000)
            embed.set_thumbnail(url=post_thumbnail)
            embed.add_field(name="Author", value="[/u/{}]({})".format(post_author, "https://reddit.com/u/{}".format(post_author)))
            embed.add_field(name="Permalink", value="{}".format(post_permalink))

            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(RedditCommands(bot))