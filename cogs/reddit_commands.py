from discord.ext import commands
import mysql
import config
import requests
import requests.auth

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
        with mysql.sqlConnection.cursor() as cursor:
            cursor.execute(config.sqlRetrieveRedditInfo)
            reddit_info = cursor.fetchall()
        mysql.sqlConnection.commit()
        cursor.close()

        client_auth = requests.auth.HTTPBasicAuth(reddit_info[0]["client_id"], reddit_info[0]["client_secret"])
        post_data = {"grant_type": "password", "username": reddit_info[0]["username"], "password": reddit_info[0]["password"]}
        user_agent = "Frosty by refekt"
        headers = {"User-Agent": user_agent}

        response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers=headers)
        token_info = response.json()

        headers = {"Authorization": "bearer {}".format(token_info["access_token"]), "User-Agent": user_agent}
        response = requests.get("https://oauth.reddit.com/r/huskers/new", headers=headers)

        print(response.json())


def setup(bot):
    bot.add_cog(RedditCommands(bot))