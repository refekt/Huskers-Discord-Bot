from discord.ext import commands
# from discord.ext import tasks
import discord
import mysql
import config
import requests
import requests.auth

globalRate = 3
globalPer = 30
max_posts = 5
reddit_footer = "/r/Huskers Post created by Bot Frost | ID: "
reddit_reactions = ("⬆", "⬇")

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

    access_token_response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
    token_info = access_token_response.json()

    me_response = requests.get(url="https://www.reddit.com/api/v1/me.json", auth=client_auth, headers=headers)
    me_info = me_response.json()

    try:
        print(me_info["modhash"])
    except:
        pass

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


def vote_post(vote: str, id: str):
    token_info = reddit_oauth()
    headers = {"Authorization": "bearer {}".format(token_info["access_token"]), "User-Agent": user_agent}
    url = "https://oauth.reddit.com/api/vote?dir={}&id={}&rank=2".format(vote, id)
    requests.post(url=url, headers=headers)


def build_post_info(arg):
    if arg["data"]["thumbnail"] in ("self", "default"):
        post_thumbnail = "https://i.imgur.com/Ah3x5NA.png"
    else:
        post_thumbnail = arg["data"]["thumbnail"]
    post_info = dict(
        title=arg["data"]["title"],
        author=arg["data"]["author"],
        ups=arg["data"]["ups"],
        downs=arg["data"]["downs"],
        permalink=arg["data"]["permalink"],
        thumbnail=post_thumbnail,
        num_comments=arg["data"]["num_comments"],
        name=arg["data"]["name"]
    )

    return post_info


async def add_reactions(message: discord.Message, reactions):
    for reaction in reactions:
        await message.add_reaction(reaction)


def build_embed(post_info):
    embed = discord.Embed(title="⬆ {} ⬇ {} - {}".format(post_info["ups"], post_info["downs"], post_info["title"][0:230]), color=0xFF0000)
    embed.set_thumbnail(url=post_info["thumbnail"])
    embed.set_footer(text="{}{}".format(reddit_footer, post_info["name"]))
    embed.add_field(name="Author", inline=True, value="[/u/{}]({})".format(post_info["author"], "https://reddit.com/u/{}".format(post_info["author"])))
    embed.add_field(name="Permalink", inline=True, value="[{}](https://reddit.com{})".format(post_info["permalink"], post_info["permalink"]))
    embed.add_field(name="Comments", inline=True, value=post_info["num_comments"])
    return embed


class RedditCommands(commands.Cog, name="Reddit Commands"):
    # def __init__(self, bot):
    #     self.bot = bot
    #     self.bg_recent.start()
    #
    # def cog_unload(self):
    #     self.bg_recent.stop()
    #
    # @tasks.loop(seconds=10)
    # async def bg_recent(self, ctx: discord.Message, count=3):
    #     """Outputs the most recent submissions on r/Huskers. Default is 3."""
    #     print("CTX: {}".format(ctx))
    #
    #     # if ctx is None:
    #     #     ctx = client.get_channel(595705205069185047)  #593984711706279937)  # Bot channel
    #
    #     posts = recent_posts(count)
    #     if check_if_error(posts):
    #         await ctx.send(reddit_error_message)
    #         return
    #
    #     for index, post in enumerate(posts["data"]["children"]):
    #         if index == count:
    #             break
    #
    #         post_info = build_post_info(post)
    #         embed = build_embed(post_info)
    #
    #         msg = await ctx.send(embed=embed)
    #         # await add_reactions(message=msg, reactions=reddit_reactions)
    #
    # @bg_recent.before_loop
    # async def before_bg_recent(self):
    #     print("Starting `recent` loop")
    #     pass
    #
    # @bg_recent.after_loop
    # async def after_bg_recent(self):
    #     print("Stopping `recent` loop")
    #     pass

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
            embed = build_embed(post_info)

            msg = await ctx.send(embed=embed)
            # await add_reactions(message=msg, reactions=reddit_reactions)

    @reddit.command(aliases=["g",])
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
                embed = build_embed(post_info)
                await edit_msg.edit(content="", embed=embed)
                return

        await edit_msg.edit(content="No game day threads found!")
        # await add_reactions(message=edit_msg, reactions=reddit_reactions)

    @reddit.command(aliases=["p",])
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
                embed = build_embed(post_info)
                await edit_msg.edit(content="", embed=embed)
                return

        await edit_msg.edit(content="No post game threads found!")
        # await add_reactions(message=edit_msg, reactions=reddit_reactions)

    @reddit.command(aliases=["w",])
    async def weekly(self, ctx):
        """Outputs the current weekly game discussion on r/Huskers."""
        thread_titles = "weekly discussion thread -"

        edit_msg = await ctx.send("Loading...")

        posts = recent_posts(100)
        if check_if_error(posts):
            await ctx.send(reddit_error_message)
            return

        for index, post in enumerate(posts["data"]["children"]):
            post_info = build_post_info(post)
            if post_info["title"].lower().startswith(thread_titles):
                embed = build_embed(post_info)
                await edit_msg.edit(content="", embed=embed)
                return

        await edit_msg.edit(content="No post game threads found!")
        # await add_reactions(message=edit_msg, reactions=reddit_reactions)


def setup(bot):
    bot.add_cog(RedditCommands(bot))