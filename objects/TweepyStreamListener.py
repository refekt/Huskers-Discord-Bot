import ast
import logging

import tweepy

logger = logging.getLogger(__name__)


class MyTweet(tweepy.Tweet):
    def __init__(self, data):
        super().__init__(data)
        for key, value in data.items():
            setattr(self, key, value)


class TwitterStreamListenerV2(tweepy.StreamingClient):
    def __init__(self, bearer_token, **kwargs):
        super().__init__(bearer_token, **kwargs)
        logger.info("StreamingListenerV2 initialized")

    def on_connect(self):
        logger.info("Twitter Stream Listener v2 is connected")

    def on_disconnect(self):
        logger.info("Twitter Stream Listener v2 disconnected")

    def on_keep_alive(self):
        logger.info("Twitter Stream Listener v2 keep alive")

    def on_tweet(self, tweet):
        logger.info(f"Twitter Stream Listener v2 Tweet received\n{tweet}")

    def on_errors(self, errors):
        logger.info(f"Twitter Stream Listener v2 Error received\n{errors}")

    def on_closed(self, response):
        logger.info(f"Twitter Stream Listener v2 closed\n{response}")

    def on_exception(self, exception):
        logger.info(f"Twitter Stream Listener v2 Exception\n{exception}")

    def on_includes(self, includes):
        logger.info(f"Twitter Stream Listener v2 Includes\n{includes}")

    def on_response(self, response):
        logger.info(f"Twitter Stream Listener v2 Response\n{response}")

    def on_data(self, raw_data):
        processed_data = ast.literal_eval(raw_data)
        tweet = MyTweet()
        logger.info(f"Twitter Stream Listener v2 Raw Data\n{raw_data}")

    def on_connection_error(self):
        logger.info(f"Twitter Stream Listener v2 Connection Error")

    def on_matching_rules(self, matching_rules):
        logger.info(f"Twitter Stream Listener v2 Matching Rules\n{matching_rules}")

    def on_request_error(self, status_code):
        logger.info(f"Twitter Stream Listener v2 Request Error\n{status_code}")
