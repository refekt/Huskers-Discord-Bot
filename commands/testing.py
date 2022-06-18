import json
import logging
import sys
from typing import Union

import tweepy
from tweepy import Response

from helpers.constants import (
    TWITTER_BEARER,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_QUERY_MAX,
)

logging.basicConfig(
    # format="[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s",
    datefmt="%X %x",
    level=logging.DEBUG,
    encoding="utf-8",
    stream=sys.stdout,
)
tweepy_logger = logging.getLogger("tweepy")
tweepy_logger.setLevel(logging.DEBUG)

# handler = logging.FileHandler(filename="tweepy.log")
# tweepy_logger.addHandler(handler)


class MyTweet(object):
    def __init__(self, tweet_data) -> None:
        self.data = None
        self.includes = None
        self.matching_rules = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetMediaData(object):
    def __init__(self, tweet_data) -> None:
        self.url = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetQuoteData(object):
    def __init__(self, tweet_data) -> None:
        self.id = None
        self.text = None
        self.author_id = None
        for key in tweet_data:
            setattr(self, key, tweet_data[key])


class TweetUserData(object):
    def __init__(self, data) -> None:
        self.public_metrics = None
        self.verified = None
        self.profile_image_url = None
        self.name = None
        self.username = None
        self.followers = None
        self.following = None
        self.tweet_count = None
        self.listed_count = None
        for key in data:
            setattr(self, key, data[key])


def send_tweet_alert(message) -> None:
    print("send_tweet_alert", message)


def send_tweet(tweet: MyTweet) -> None:
    author = None  # noqa
    for user in tweet.includes["users"]:
        if tweet.data["author_id"] == user["id"]:
            author: TweetUserData = TweetUserData(user)
            break

    medias = []
    if "media" in tweet.includes:
        for item in tweet.includes["media"]:
            medias.append(TweetMediaData(item))

    quotes = []
    if "tweets" in tweet.includes:
        for item in tweet.includes["tweets"]:
            quotes.append(TweetQuoteData(item))

    print("send_tweet", tweet)


class TestStreamClient(tweepy.StreamingClient):
    def __init__(
        self,
        bearer_token,
        **kwargs,
    ) -> None:
        super().__init__(bearer_token, **kwargs)
        pass

    def remove_all_rules(self) -> None:
        raw_rules: Union[dict, Response, Response] = self.get_rules()
        if raw_rules.data is not None:
            ids = [rule.id for rule in raw_rules.data]
            self.delete_rules(ids)

    def on_keep_alive(self) -> None:
        print("on_keep_alive")

    def on_tweet(self, tweet) -> None:
        print("on_tweet", tweet)

    def on_response(self, response) -> None:
        print("on_response", response)

    def on_includes(self, includes) -> None:
        print("on_includes", includes)

    def on_matching_rules(self, matching_rules) -> None:
        print("on_matching_rules", matching_rules)

    def on_connect(self) -> None:
        pass

    def on_request_error(self, status_code) -> None:
        self.remove_all_rules()
        print("on_request_error", status_code)

    def on_connection_error(self) -> None:
        self.remove_all_rules()
        print("on_connection_error")

    def on_disconnect(self) -> None:
        self.remove_all_rules()
        print("on_disconnect")

    def on_errors(self, errors) -> None:
        self.remove_all_rules()
        print("on_errors", errors)

    def on_closed(self, response) -> None:
        self.remove_all_rules()
        print("on_closed", response)

    def on_exception(self, exception) -> None:
        self.remove_all_rules()
        print("on_exception", exception)

    def on_data(self, raw_data) -> None:
        processed_data = json.loads(raw_data)
        send_tweet(MyTweet(processed_data))
        print("on_data")


def start_twitter_stream() -> None:
    tweeter_stream = TestStreamClient(
        bearer_token=TWITTER_BEARER,
        wait_on_rate_limit=True,
        # max_retries=3,
    )
    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()
    if raw_rules.data is not None:
        ids = [rule.id for rule in raw_rules.data]
        tweeter_stream.delete_rules(ids)

    tweeter_client = tweepy.Client(TWITTER_BEARER)
    list_members = tweeter_client.get_list_members(TWITTER_HUSKER_MEDIA_LIST_ID)

    rule_query = "from:ayy_gbr OR "

    rules: list[str] = []
    append_str: str = ""

    for member in list_members[0]:
        append_str = f"from:{member['username']} OR "

        if len(rule_query) + len(append_str) > TWITTER_QUERY_MAX:
            rule_query = rule_query[:-4]  # Get rid of ' OR '
            rules.append(rule_query)
            rule_query = ""

        rule_query += append_str

    rule_query = rule_query[:-4]  # Get rid of ' OR '
    rules.append(rule_query)

    del list_members, member, tweeter_client, append_str

    for stream_rule in rules:
        tweeter_stream.add_rules(tweepy.StreamRule(stream_rule))

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()

    tweeter_stream.filter(
        expansions=[
            "attachments.media_keys",
            "attachments.poll_ids",
            "author_id",
            "entities.mentions.username",
            "geo.place_id",
            "in_reply_to_user_id",
            "referenced_tweets.id",
            "referenced_tweets.id.author_id",
        ],
        media_fields=[
            # "alt_text",
            "duration_ms",
            "height",
            "media_key",
            "preview_image_url",
            "public_metrics",
            "type",
            "url",
            "width",
        ],
        # place_fields=[
        #     "contained_within",
        #     "country",
        #     "country_code",
        #     "full_name",
        #     "geo",
        #     "id",
        #     "name",
        #     "place_type",
        # ],
        # poll_fields=[
        #     "duration_minutes",
        #     "end_datetime",
        #     "id",
        #     "options",
        #     "voting_status",
        # ],
        tweet_fields=[
            "attachments",
            "author_id",
            "context_annotations",
            "conversation_id",
            "created_at",
            "entities",
            "geo",
            "id",
            "in_reply_to_user_id",
            "lang",
            "possibly_sensitive",
            "public_metrics",
            "referenced_tweets",
            "reply_settings",
            "source",
            "text",
            "withheld",
        ],
        user_fields=[
            "created_at",
            "description",
            "entities",
            "id",
            "location",
            "name",
            "pinned_tweet_id",
            "profile_image_url",
            "protected",
            "public_metrics",
            "url",
            "username",
            "verified",
            "withheld",
        ],
        threaded=True,
    )
    pass


if __name__ == "__main__":
    start_twitter_stream()
