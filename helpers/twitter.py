import logging
import os
import pathlib
from typing import Union, Optional

import discord
import tweepy
import tweepy.asynchronous

from tweepy import Response

from helpers.constants import (
    TWITTER_BEARER,
    TWITTER_BLOCK16_SCREENANME,
    TWITTER_EXPANSIONS,
    TWITTER_HUSKER_COACH_LIST_ID,
    TWITTER_HUSKER_MEDIA_LIST_ID,
    TWITTER_MEDIA_FIELDS,
    TWITTER_MONITOR_BEARER,
    TWITTER_QUERY_MAX,
    TWITTER_TWEET_FIELDS,
    TWITTER_USER_FIELDS,
)
from objects.Logger import discordLogger, is_debugging
from objects.TweepyFollowerMonitor import TwitterFollowerMonitor
from objects.TweepyStreamListener import StreamClientV2

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)


async def start_twitter_stream(client: discord.Client) -> None:
    logger.info("Bot is starting the Twitter stream")

    tweeter_stream = StreamClientV2(
        bearer_token=TWITTER_BEARER,
        discord_client=client,
        wait_on_rate_limit=True,
    )

    logger.debug("Twitter stream client created")

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()
    if raw_rules.data is not None:
        ids = [rule.id for rule in raw_rules.data]
        tweeter_stream.delete_rules(ids)

    logger.debug("Previous Twitter Stream rules deleted")

    tweeter_client = tweepy.Client(TWITTER_BEARER)
    list_members = tweeter_client.get_list_members(str(TWITTER_HUSKER_MEDIA_LIST_ID))

    logger.debug("Collected usernames from the Husker Media Twitter List")

    rule_query = ""
    rules: list[str] = []

    if is_debugging():
        rule_query = "from:ayy_gbr OR "

    rule_query += f"from:{TWITTER_BLOCK16_SCREENANME} OR "

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
        tweeter_stream.add_rules(tweepy.StreamRule(stream_rule, tag="husker-media"))

    raw_rules: Union[dict, Response, Response] = tweeter_stream.get_rules()

    auths: Union[str, list[str]] = ""

    for rule in raw_rules.data:
        auths += rule.value + " OR "

    auths = auths[:-4]
    auths = auths.replace("from:", "@")
    auths = auths.split(" OR ")
    auths = ", ".join(auths)

    if raw_rules.data is not None:
        logger.debug(f"Twitter Stream rules: {auths}")
    else:
        logger.debug("No rules found")

    tweeter_stream.filter(
        expansions=TWITTER_EXPANSIONS,
        media_fields=TWITTER_MEDIA_FIELDS,
        tweet_fields=TWITTER_TWEET_FIELDS,
        user_fields=TWITTER_USER_FIELDS,
        threaded=True,
    )


async def start_twitter_monitors(discord_client: discord.Client) -> None:
    debug_logger: logging.Logger = logging.getLogger("twitter_monitor_debug")
    debug_logger.setLevel(level=logging.DEBUG)

    format_string: str = "[%(asctime)s] %(levelname)s :: %(name)s :: %(module)s :: func/%(funcName)s :: Ln/%(lineno)d :: %(message)s"
    formatter: logging.Formatter = logging.Formatter(format_string)

    filename: pathlib.Path = pathlib.Path("twitter_monitor.log")
    full_path: str = os.path.join(filename.parent.resolve(), "logs", filename)

    file_handler: logging.FileHandler = logging.FileHandler(
        filename=full_path, mode="a+"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level=logging.DEBUG)

    tweepy_client = tweepy.asynchronous.AsyncClient(
        bearer_token=TWITTER_MONITOR_BEARER, wait_on_rate_limit=True
    )

    logger.debug("Collecting Twitter Users from Husker Coaches list")

    # Get members from twitter list
    twitter_list: tweepy.Response = await tweepy_client.get_list(
        id=TWITTER_HUSKER_COACH_LIST_ID
    )
    _raw_list_members: tweepy.Response = await tweepy_client.get_list_members(
        twitter_list.data.id
    )

    # Create monitors to run async and threaded
    monitors: Optional[list[TwitterFollowerMonitor]] = []
    for user in _raw_list_members.data:
        monitors.append(
            TwitterFollowerMonitor(
                discord_client=discord_client,
                tweepy_client=tweepy_client,
                twitter_user=user,
            )
        )

    logger.debug("Twitter Users from Husker Coaches list collected")

    # Compile followers for each monitor (Twitter user)
    logger.debug("Starting to compile Husker Coaches followers")

    for monitor in monitors:
        await monitor.twitter_user.compile()

        logger.debug(f"Monitor compiled for @{monitor.twitter_user.username}")

    logger.debug(f"There were {len(monitors)} monitors compiled.")

    # Compiling and starting separate on purpose

    # Start each monitor
    logger.debug("Starting monitors")

    for monitor in monitors:
        # TODO Stagger the starts to offset API calls to prevent rate limiting

        await monitor.start()
        logger.debug(f"Monitor for @{monitor.twitter_user.username} started")

    logger.debug(f"All {len(monitors)} monitors started.")
