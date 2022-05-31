# TODO
# N/A
# TODO
import tweepy

from helpers.constants import (
    TWITTER_BEARER,
    TWITTER_V2_CLIENT_ID,
    TWITTER_V2_CLIENT_SECRET,
    TWITTER_TOKEN_SECRET,
    TWITTER_TOKEN,
    TWITTER_KEY,
    TWITTER_SECRET_KEY,
)

twitter_client = tweepy.Client(
    # consumer_key=TWITTER_V2_CLIENT_ID,
    # consumer_secret=TWITTER_V2_CLIENT_SECRET,
    # access_token=TWITTER_TOKEN,
    # access_token_secret=TWITTER_TOKEN_SECRET,
    bearer_token=TWITTER_BEARER,
)

streaming_client = tweepy.StreamingClient(TWITTER_BEARER)
print("Done 1")
print(twitter_client.search_spaces("huskers"))
print("Done 2")
