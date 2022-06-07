import logging
from datetime import datetime
from typing import Union

import discord
import validators

from helpers.constants import (
    BOT_DISPLAY_NAME,
    BOT_FOOTER_BOT,
    BOT_GITHUB_URL,
    BOT_ICON_URL,
    BOT_THUMBNAIL_URL,
    DT_TWEET_FORMAT,
    TZ,
)
from helpers.misc import discordURLFormatter
from objects.Exceptions import CommandException

logger = logging.getLogger(__name__)
__all__ = ["buildEmbed", "buildTweetEmbed"]

# https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
title_limit = name_limit = field_name_limit = 256
desc_limit = 4096
footer_limit = 2048
fields_limt = 25
field_value_limit = 1024
embed_max = 6000


def buildEmbed(title: str, **kwargs) -> Union[discord.Embed, None]:
    logger.info("Creating a normal embed")

    assert title is not None, CommandException("Title must not be blank!")

    dtNow = datetime.now().astimezone(tz=TZ)  # .isoformat()

    if "color" in kwargs.keys():
        if "description" in kwargs.keys():
            e = discord.Embed(
                title=title[:title_limit],
                description=kwargs["description"][:desc_limit],
                color=kwargs["color"],
                timestamp=dtNow,
            )
        else:
            e = discord.Embed(
                title=title[:title_limit], color=kwargs["color"], timestamp=dtNow
            )
    else:
        if "description" in kwargs.keys():
            e = discord.Embed(
                title=title[:title_limit],
                description=kwargs["description"][:desc_limit],
                color=0xD00000,
            )
        else:
            e = discord.Embed(title=title[:title_limit], color=0xD00000)

    if "footer" in kwargs.keys():
        e.set_footer(text=kwargs.get("footer")[:footer_limit], icon_url=BOT_ICON_URL)
    else:
        e.set_footer(
            text=BOT_FOOTER_BOT[:footer_limit],
            icon_url=BOT_ICON_URL,
        )

    if "image" in kwargs.keys() and validators.url(kwargs.get("image")):
        e.set_image(url=kwargs.get("image"))

    if "author" in kwargs.keys():
        e.set_author(name=kwargs.get("author")[:name_limit], url="", icon_url="")
    else:
        e.set_author(
            name=BOT_DISPLAY_NAME[:name_limit], url=BOT_GITHUB_URL, icon_url=""
        )

    if "thumbnail" in kwargs.keys() and validators.url(kwargs.get("thumbnail")):
        e.set_thumbnail(url=kwargs.get("thumbnail"))
    else:
        e.set_thumbnail(url=BOT_THUMBNAIL_URL)

    if "fields" in kwargs.keys():
        for index, field in enumerate(kwargs.get("fields")):
            if index == fields_limt:
                break

            e.add_field(
                name=field["name"][:field_name_limit],
                value=field["value"][:field_value_limit],
                inline=field.get("inline", False),
            )
    if len(e) > embed_max:
        logger.exception("Embed is too big!")
        raise
    else:
        logger.info("Returning a normal embed")
        return e


def buildTweetEmbed(
    author_metrics: dict,
    name: str,
    profile_image_url: str,
    source: str,
    text: str,
    tweet_created_at: datetime,
    tweet_id: str,
    tweet_metrics: dict,
    username: str,
    verified: bool,
    medias: list = None,
    quotes: list = None,
    urls: dict = None,
):
    embed = buildEmbed(
        title="",
        fields=[
            dict(
                name="Message",
                value=text,
            ),
            dict(
                name="Tweet URL",
                value=f"https://twitter.com/{username}/status/{tweet_id}",
            ),
        ],
    )

    if urls:
        for url in urls["urls"]:  # TODO KeyError is raising
            if (
                medias
            ):  # Avoid duplicating media embeds. Also, there's no "title" field when the URL is from a media embed
                if not url.get("media_key"):
                    logger.info("Skipping url because media_key does not exist")
                    break
                if url["media_key"] in [media.media_key for media in medias]:
                    logger.info("Skipping duplicate media_key from URLs")
                    break

            # Quote tweets don't have title in the url item
            if not url.get("title"):
                break

            embed.add_field(
                name="Embeded URL",
                value=discordURLFormatter(
                    display_text=url["title"], url=url["expanded_url"]
                ),
            )

    if medias:
        for index, item in enumerate(medias):
            embed.add_field(
                name="Embeded Image",
                value=discordURLFormatter(f"Image #{index+1}", item.url),
            )

    if quotes:
        for item in quotes:
            embed.add_field(
                name="Quoted Tweet",
                value=item.text,
            )

    embed.set_author(
        name=f"{name}{' ☑️' if verified else ' '}(@{username}) • Followers: {author_metrics['followers_count']} • Tweets: {author_metrics['tweet_count']}",
        url=f"https://twitter.com/{username}",
        icon_url=profile_image_url,
    )
    embed.set_footer(
        text=f"Sent via {source} at {tweet_created_at.strftime(DT_TWEET_FORMAT)} • Retweets: {tweet_metrics['retweet_count']} • Replies: {tweet_metrics['reply_count']} • Likes: {tweet_metrics['like_count']} • Quotes: {tweet_metrics['quote_count']}"[
            :footer_limit
        ],
    )
    embed.set_thumbnail(url=profile_image_url)
    return embed


logger.info(f"{str(__name__).title()} module loaded!")
