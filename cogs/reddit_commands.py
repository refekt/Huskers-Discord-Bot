from discord.ext import commands
import discord
import mysql
import config
import requests
import requests.auth

globalRate = 3
globalPer = 30
max_posts = 5

user_agent = "Frosty by refekt"
reddit_error_message = "An error occurred retrieving posts from reddit!"


def reddit_oauth():
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


def check_if_error(arg):
    try:
        if arg["error"] == 400:
            return True
    except:
        return False


def recent_posts(count=25):
    token_info = reddit_oauth()
    headers = {"Authorization": "bearer {}".format(token_info["access_token"]), "User-Agent": user_agent}
    response = requests.get("https://oauth.reddit.com/r/huskers/new?limit={}".format(count), headers=headers)
    posts = response.json()

    return posts


def build_post_info(arg):
    if arg["data"]["thumbnail"] == "self":
        post_thumbnail = "https://i.imgur.com/Ah3x5NA.png"
    else:
        post_thumbnail = arg["data"]["thumbnail"]
    post_info = dict(title=arg["data"]["title"], author=arg["data"]["author"], ups=arg["data"]["ups"], downs=arg["data"]["downs"], permalink=arg["data"]["permalink"], thumbnail=post_thumbnail)

    return post_info


class RedditCommands(commands.Cog, name="Reddit Commands"):
    @commands.group()
    @commands.cooldown(rate=globalRate, per=globalPer, type=commands.BucketType.user)
    async def reddit(self, ctx):
        """Interacts with the r/Huskers subreddit"""
        pass

    @reddit.command()
    async def recent(self, ctx, count=3):
        """Outputs the most recent submissions on r/Huskers. Default is 3."""
        posts = recent_posts(count)
        if check_if_error(posts):
            await ctx.send(reddit_error_message)
            return

        for index, post in enumerate(posts["data"]["children"]):
            if index == count:
                break

            post_info = build_post_info(post)

            embed = discord.Embed(title="⬆ {} ⬇ {} - {}".format(post_info["ups"], post_info["downs"], post_info["title"]), color=0xFF0000)
            embed.set_thumbnail(url=post_info["thumbnail"])
            embed.add_field(name="Author", value="[/u/{}]({})".format(post_info["author"], "https://reddit.com/u/{}".format(post_info["author"])))
            embed.add_field(name="Permalink", value="[{}](https://reddit.com{})".format(post_info["permalink"], post_info["permalink"]))

            await ctx.send(embed=embed)

    @reddit.command()
    async def gameday(self, ctx):
        """Outputs the most recent game day thread on r/Huskers."""
        thread_titles = ("pregame thread -", "game thread -")

        edit_msg = await ctx.send("Loading...")

        posts = recent_posts(100)
        if check_if_error(posts):
            await ctx.send(reddit_error_message)
            return

        for index, post in enumerate(posts["data"]["children"]):
            post_info = build_post_info(post)
            if post_info["title"].lower().startswith(thread_titles[0]) or post_info["title"].lower().startswith(thread_titles[1]):
                embed = discord.Embed(title="⬆ {} ⬇ {} - {}".format(post_info["ups"], post_info["downs"], post_info["title"]), color=0xFF0000)
                embed.set_thumbnail(url=post_info["thumbnail"])
                embed.add_field(name="Author", value="[/u/{}]({})".format(post_info["author"], "https://reddit.com/u/{}".format(post_info["author"])))
                embed.add_field(name="Permalink", value="[{}](https://reddit.com{})".format(post_info["permalink"], post_info["permalink"]))

                await edit_msg.edit(content="", embed=embed)
                return

        await edit_msg.edit(content="No game day threads found!")

    @reddit.command()
    async def postgame(self, ctx):
        """Outputs the most recent postt game day thread on r/Huskers."""
        thread_titles = "post game thread -"

        edit_msg = await ctx.send("Loading...")

        posts = recent_posts(100)
        if check_if_error(posts):
            await ctx.send(reddit_error_message)
            return

        for index, post in enumerate(posts["data"]["children"]):
            post_info = build_post_info(post)
            if post_info["title"].lower().startswith(thread_titles):
                embed = discord.Embed(title="⬆ {} ⬇ {} - {}".format(post_info["ups"], post_info["downs"], post_info["title"]), color=0xFF0000)
                embed.set_thumbnail(url=post_info["thumbnail"])
                embed.add_field(name="Author", value="[/u/{}]({})".format(post_info["author"], "https://reddit.com/u/{}".format(post_info["author"])))
                embed.add_field(name="Permalink", value="[{}](https://reddit.com{})".format(post_info["permalink"], post_info["permalink"]))

                await edit_msg.edit(content="", embed=embed)
                return

        await edit_msg.edit(content="No post game threads found!")


def setup(bot):
    bot.add_cog(RedditCommands(bot))