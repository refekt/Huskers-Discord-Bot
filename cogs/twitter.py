import twitter
from discord.ext import commands

from utils.consts import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_TOKEN_KEY, TWITTER_TOKEN_SECRET


def setup_twitter():
    return twitter.Api(
        consumer_key=TWITTER_CONSUMER_KEY,
        consumer_secret=TWITTER_CONSUMER_SECRET,
        access_token_key=TWITTER_TOKEN_KEY,
        access_token_secret=TWITTER_TOKEN_SECRET
    )


class TwitterCommands(commands.Cog, name="Twitter Commands"):
    pass


def setup(bot):
    bot.add_cog(TwitterCommands(bot))