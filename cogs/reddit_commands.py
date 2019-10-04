import praw
import discord
from discord.ext import commands
import mysql
import config

globalRate = 3
globalPer = 30
max_posts = 5


class RedditCommands(commands.Cog, name="Reddit Commands"):
    @commands.group()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def sub(self, ctx):
        pass

    @sub.command()
    async def recent(self, ctx):
        edit_msg = await ctx.send("Loading...")

        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveRedditInfo)
            reddit_info = cursor.fetchone()
        mysql.sqlConnection.commit()
        cursor.close()

        reddit = praw.Reddit(
            client_id=reddit_info["client_id"],
            client_secret=reddit_info["client_secret"],
            user_agent=reddit_info["user_agent"],
            username=reddit_info["username"],
            password=reddit_info["password"]
        )

        subreddit = reddit.subreddit("huskers")
        posts = []

        limit = 99
        for index, submissions in enumerate(subreddit.stream.submissions()):
            posts.append([submissions.author, submissions.title, submissions.permalink, submissions.ups, submissions.downs, submissions.thumbnail])
            if index == limit:
                break

        posts.reverse()

        await edit_msg.delete()

        limit = 4
        for index, post in enumerate(posts):
            url_profile = "https://reddit.com/u/{}".format(post[0])
            url_permalink = "https://reddit.com{}".format(post[2])

            embed = discord.Embed(title="{}".format(post[1]), color=0xFF0000)
            if post[5] == "self":
                embed.set_thumbnail(url="https://i.imgur.com/aaqkw35.png")
            else:
                embed.set_thumbnail(url=post[5])
            embed.add_field(name="{} ⬆ {} ⬇".format(post[3], post[4]), inline=False, value="Permalink: [Click]({})\nAuthor: [/u/{}]({})\n".format(url_permalink, post[0], url_profile))

            await ctx.send(embed=embed)

            if index == limit:
                break


def setup(bot):
    bot.add_cog(RedditCommands(bot))