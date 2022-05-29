import asyncio
import time

import tweepy


class TwitterStreamListener(tweepy.Stream):
    def __init__(
        self,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
        message_func,
        alert_func,
        loop,
    ):
        super().__init__(
            consumer_key, consumer_secret, access_token, access_token_secret
        )
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.message_func = message_func
        self.alert_func = alert_func
        self.loop = loop
        self.cooldown = 1

    def reset_cooldown(self):
        self.cooldown = 0

    def process_cooldown(self):
        # log(f"Pausing for {self.cooldown} seconds", 1)
        # asyncio.sleep(self.cooldown)
        time.sleep(self.cooldown)
        self.cooldown = min(self.cooldown * 2, 600)  # 10 minute max
        # log(f"Pause complete. New timer is {self.cooldown} seconds", 1)

    def send_message(self, tweet):
        # log("Sending a new tweet", 1)
        future = asyncio.run_coroutine_threadsafe(self.message_func(tweet), self.loop)
        future.result()

    def send_alert(self, message):
        # log("Sending an alert", 1)
        future = asyncio.run_coroutine_threadsafe(self.alert_func(message), self.loop)
        future.result()

    def on_connect(self):
        # log(f"Stream connected", 0)
        self.send_alert(f"Stream connected!")
        self.reset_cooldown()

    def on_status(self, status):
        # if not status.retweeted and status.in_reply_to_status_id is None and not hasattr(status, "retweeted_status"):
        # log(f"Status received", 1)
        self.send_message(status)

    def on_warning(self, notice):
        # log(f"Warning: {notice}", 1)
        ...

    def on_connection_error(self):
        # log(f"Connection error", 1)
        self.send_alert(f"Stream failed to connect.")
        self.process_cooldown()
        # return True  # Reconnect

    def on_request_error(self, status_code):
        # log(f"Request Error: {status_code}", 1)
        if status_code == 420:
            rl_msg = (
                f"Stream is being rate limited. Retrying in {self.cooldown} seconds..."
            )
            # log(
            #     rl_msg,
            #     1,
            # )
            self.send_alert(rl_msg)
            self.process_cooldown()
        else:
            # log(f"Request Error: {status_code}", 1)
            return True  # Reconnect

    async def on_disconnect_message(self, message):
        # log(f"Stream disconnected. Notice: {message}", 1)
        self.send_alert(
            f"Stream was disconnected. Retrying in {self.cooldown} seconds..."
        )
        self.process_cooldown()
        self.send_alert("Stream attempting to reconnect!")

        return True  # Reconnect

    def on_keep_alive(self):
        # log("Stream has received a keep alive signal.", 1)
        self.process_cooldown()

    def on_exception(self, exception):
        # log(f"Exception: {exception}", 1)
        self.process_cooldown()
        return True

    def on_limit(self, track):
        # log(
        #     f"Stream is being rate limited. Unable to deliver {track} tweets",
        #     1,
        # )
        self.send_alert(
            f"Stream is being rate limited. Unable to deliver {track} tweets"
        )
        self.process_cooldown()