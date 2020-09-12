import tweepy
from discord.ext import commands

from utils.consts import TWITTER_TOKEN_SECRET, TWITTER_TOKEN_KEY, TWITTER_CONSUMER_SECRET, TWITTER_CONSUMER_KEY
from utils.embed import build_embed


def twitter_api():
    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_TOKEN_KEY, TWITTER_TOKEN_SECRET)

    return tweepy.API(auth)


class WebhookCommands(commands.Cog, name="Webhook Commands"):

    @commands.command()
    async def webhooktest(self, ctx):
        # TODO This grabs the "stream" of whatever you want to search for, but I am having troubles passing it from sync to async.
        class MyStreamListener(tweepy.StreamListener):
            def on_status(self, status):
                print(status.text)

        myStream = tweepy.Stream(auth=twitter_api().auth, listener=MyStreamListener())

        search_tearms = ["huskers", "nebraska", "big ten", "b1g", "gbr", "frost"]

        myStream.filter(track=search_tearms, is_async=True)

    @commands.command()
    async def searchtest(self, ctx):
        auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
        auth.set_access_token(TWITTER_TOKEN_KEY, TWITTER_TOKEN_SECRET)

        api = tweepy.API(auth)

        list_id = 1223689242896977922

        # public_tweets = api.home_timeline(count=2)
        list_tweets = api.list_timeline(list_id=list_id, count=2)

        for tweet in list_tweets:
            await ctx.send(embed=build_embed(
                title=f"Tweet from: @{tweet.author.screen_name}",
                fields=[
                    ["Content", tweet.text]
                ],
                inline=True,
                thumbnail=tweet.author.profile_image_url,
                url=f"https://twitter.com/{tweet.author.screen_name}/status/{tweet.id}"
            ))


def setup(bot):
    bot.add_cog(WebhookCommands(bot))
