import twitter
# from discord.ext import commands

from utils.consts import TWITTER_TOKEN_SECRET, TWITTER_TOKEN_KEY, TWITTER_CONSUMER_SECRET, TWITTER_CONSUMER_KEY
from utils.consts import CHAN_TWITTERVERSE, CHAN_TEST_SPAM
from utils.embed import build_embed


async def start_twitter_stream(client):

    print(f"Loading Twitter stream...")

    api = twitter.Api(
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token_key=TWITTER_TOKEN_KEY,
        access_token_secret=TWITTER_TOKEN_SECRET
    )

    twitter_stream = api.GetStreamFilter(
        track=["nebraska", "huskers", "gbr"],
        languages=["en"]
    )

    print(twitter_stream)

    chan = client.get_channel(CHAN_TEST_SPAM)

    for tweet in twitter_stream:
        await chan.send(
            embed=build_embed(
                title=f"Tweet by: @{tweet['user']['screen_name']}",
                description=f"[Twitter link](https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id']}) | {tweet['created_at']}",
                fields=[
                    ["Content", f"{tweet['text']}"]
                ],
                thumbnail=tweet["user"]["profile_image_url"],
                footer="🎈 = General 🌽 = Scott's Tots"
            )
        )

# class WebhookCommands(commands.Cog, name="Webhook Commands"):
#
#     @commands.command()
#     async def twitter_package(self, ctx):
#         api = twitter.Api(
#             consumer_key=TWITTER_CONSUMER_KEY,
#             consumer_secret=TWITTER_CONSUMER_SECRET,
#             access_token_key=TWITTER_TOKEN_KEY,
#             access_token_secret=TWITTER_TOKEN_SECRET
#         )
#
#         twitter_steam = api.GetStreamFilter(
#             track=["nebraska", "huskers", "gbr"],
#             languages=["en"]
#         )
#
#         for tweet in twitter_steam:
#             await ctx.send(
#                 embed=build_embed(
#                     title=f"Tweet by: @{tweet['user']['screen_name']}",
#                     description=f"[Twitter link](https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id']}) | {tweet['created_at']}",
#                     fields=[
#                         ["Content", f"{tweet['text']}"]
#                     ],
#                     thumbnail=tweet["user"]["profile_image_url"],
#                     footer="🎈 = General 🌽 = Scott's Tots"
#                 )
#             )
#
#
# def setup(bot):
#     bot.add_cog(WebhookCommands(bot))
