import logging
from datetime import datetime
from typing import Union

import discord
import validators

# from commands.recruiting import get_faps, get_croot_predictions
from helpers.constants import (
    BOT_DISPLAY_NAME,
    BOT_FOOTER_BOT,
    BOT_GITHUB_URL,
    BOT_ICON_URL,
    BOT_THUMBNAIL_URL,
    DT_OBJ_FORMAT,
    DT_OBJ_FORMAT_TBA,
    DT_TWEET_FORMAT,
    TZ,
    DT_STR_RECRUIT,
)
from helpers.misc import discordURLFormatter
from helpers.mysql import processMySQL, sqlGetCrootPredictions
from objects.Exceptions import CommandException
from objects.Schedule import HuskerSchedule

logger = logging.getLogger(__name__)
__all__ = [
    "buildEmbed",
    "buildRecruitEmbed",
    "buildTweetEmbed",
    "collectScheduleEmbeds",
]

# https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
desc_limit = 4096
embed_max = 6000
field_value_limit = 1024
fields_limt = 25
footer_limit = 2048
title_limit = name_limit = field_name_limit = 256


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
        logger.exception("Embed is too big!", exc_info=True)
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
) -> discord.Embed:
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
    # b'{"data":{"attachments":{},"author_id":"15899943","context_annotations":[{"domain":{"id":"46","name":"Brand Category","description":"Categories within Brand Verticals that narrow down the scope of Brands"},"entity":{"id":"781974596752842752","name":"Services"}},{"domain":{"id":"47","name":"Brand","description":"Brands and Companies"},"entity":{"id":"10045225402","name":"Twitter"}}],"conversation_id":"1534359106945003520","created_at":"2022-06-08T02:18:12.000Z","entities":{"urls":[{"start":27,"end":50,"url":"https://t.co/FcWRxe2bsw","expanded_url":"https://www.google.com","display_url":"google.com","status":200,"title":"Google","description":"Search the world\'s information, including webpages, images, videos and more. Google has many special features to help you find exactly what you\'re looking for.","unwound_url":"https://www.google.com"},{"start":51,"end":74,"url":"https://t.co/0H5vssRWaK","expanded_url":"http://www.yahoo.com","display_url":"yahoo.com","status":400,"unwound_url":"http://www.yahoo.com"},{"start":75,"end":98,"url":"https://t.co/aSHcc1XbiN","expanded_url":"http://bing.com","display_url":"bing.com","status":200,"title":"The beauty that lies below","description":"Marovo Lagoon in the Solomon Islands is the larges","unwound_url":"http://www.bing.com/"}]},"geo":{},"id":"1534359106945003520","lang":"en","possibly_sensitive":false,"public_metrics":{"retweet_count":0,"reply_count":0,"like_count":0,"quote_count":0},"reply_settings":"everyone","source":"Twitter Web App","text":"Testing tweets with links. https://t.co/FcWRxe2bsw https://t.co/0H5vssRWaK https://t.co/aSHcc1XbiN"},"includes":{"users":[{"created_at":"2008-08-19T03:09:46.000Z","description":"GBR","id":"15899943","name":"Aaron","profile_image_url":"https://pbs.twimg.com/profile_images/1206047447451086848/GEMbd3wB_normal.jpg","protected":false,"public_metrics":{"followers_count":39,"following_count":563,"tweet_count":1154,"listed_count":0},"url":"","username":"ayy_gbr","verified":false}]},"matching_rules":[{"id":"1532102238562402312","tag":""}]}'
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


def collectScheduleEmbeds(year) -> list[discord.Embed]:
    scheduled_games, season_stats = HuskerSchedule(year=year)

    new_line_char = "\n"
    embeds = []

    for game in scheduled_games:
        embeds.append(
            buildEmbed(
                title=f"{game.opponent.title()}",
                description=f"Nebraska's {year}'s Record: {season_stats.wins} - {season_stats.losses}",
                thumbnail=game.icon,
                fields=[
                    dict(
                        name="Opponent",
                        value=f"{game.ranking + ' ' if game.ranking else ''}{game.opponent}",
                    ),
                    dict(
                        name="Conference Game", value="Yes" if game.conference else "No"
                    ),
                    dict(
                        name="Date/Time",
                        value=f"{game.game_date_time.strftime(DT_OBJ_FORMAT) if not game.game_date_time.hour == 21 else game.game_date_time.strftime(DT_OBJ_FORMAT_TBA)}{new_line_char}",
                    ),
                    dict(name="Location", value=game.location),
                    dict(name="Outcome", value=game.outcome if game.outcome else "TBD"),
                ],
            )
        )

    return embeds


def buildRecruitEmbed(recruit) -> discord.Embed:
    def get_all_predictions() -> str:
        get_croot_preds_response = processMySQL(
            query=sqlGetCrootPredictions,
            values=recruit.twofourseven_profile,
            fetch="all",
        )

        if get_croot_preds_response is None:
            return "There are no predictions for this recruit."
        else:
            prediction_str = f"Team: Percent (Avg Confidence)"
            for predictions in get_croot_preds_response:
                prediction_str += f"\n{predictions['team']}: {predictions['percent']:.0f}% ({predictions['confidence']:.1f})"
            prediction_str += (
                f"\nTotal Predictions: {get_croot_preds_response[0]['total']}"
            )
            return prediction_str

    def prettify_predictions():
        pretty = ""
        for item in recruit.cb_predictions:
            pretty += f"{item}\n"
        return pretty

    def prettify_experts():
        pretty = ""
        for item in recruit.cb_experts:
            pretty += f"{item}\n"
        return pretty

    def prettify_offers():
        pretty = ""
        for index, item in enumerate(recruit.recruit_interests):
            if index > 9:
                return pretty + discordURLFormatter(
                    "View remaining offers...", recruit.recruit_interests_url
                )

            pretty += f"{item.school}{' - ' + item.status if not item.status == 'None' else ''}\n"

        return pretty

    nl = "\n"
    embed = buildEmbed(
        title=f"{str(recruit.rating_stars) + '⭐ ' if recruit.rating_stars else ''}{recruit.year} {recruit.position}, {recruit.name}",
        description=f"{recruit.committed if recruit.committed is not None else ''}"
        f"{': ' + recruit.committed_school if recruit.committed_school is not None else ''} "
        f"{': ' + str(datetime.strptime(recruit.commitment_date, DT_STR_RECRUIT)) if recruit.commitment_date is not None else ''}",
        fields=[
            dict(
                name="**Biography**",
                value=f"{recruit.city}, {recruit.state}\n"
                f"School: {recruit.school}\n"
                f"School Type: {recruit.school_type}\n"
                f"Height: {recruit.height}\n"
                f"Weight: {recruit.weight}\n",
            ),
            dict(
                name="**Social Media**",
                value=f"{'[@' + recruit.twitter + '](' + 'https://twitter.com/' + recruit.twitter + ')' if not recruit.twitter == 'N/A' else 'N/A'}",
            ),
            dict(
                name="**Highlights**",
                value=f"{'[247Sports](' + recruit.twofourseven_highlights + ')' if recruit.twofourseven_highlights else '247Sports N/A'}",
            ),
            dict(
                name="**Recruit Info**",
                value=f"[247Sports Profile]({recruit.twofourseven_profile})\n"
                f"Comp. Rating: {recruit.rating_numerical if recruit.rating_numerical else 'N/A'} \n"
                f"Nat. Ranking: [{recruit.ranking_national:,}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup"
                f"={recruit.school_type.replace(' ', '')})\n"
                f"State Ranking: [{recruit.ranking_state}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup={recruit.school_type.replace(' ', '')}&State"
                f"={recruit.state_abbr})\n"
                f"Pos. Ranking: [{recruit.ranking_position}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup="
                f"{recruit.school_type.replace(' ', '')}&Position={recruit.position})\n"
                f"{'All Time Ranking: [' + recruit.ranking_all_time + '](https://247sports.com/Sport/Football/AllTimeRecruitRankings/)' + nl if recruit.ranking_all_time else ''}"
                f"{'Early Enrollee' + nl if recruit.early_enrollee else ''}"
                f"{'Early Signee' + nl if recruit.early_signee else ''}"
                f"{'Walk-On' + nl if recruit.walk_on else ''}",
            ),
            dict(
                name="**Expert Averages**",
                value=f"{prettify_predictions() if recruit.cb_predictions else 'N/A'}",
            ),
            dict(
                name="**Lead Expert Picks**",
                value=f"{prettify_experts() if recruit.cb_experts else 'N/A'}",
            ),
            dict(
                name="**Offers**",
                value=f"{prettify_offers() if recruit.recruit_interests else 'N/A'}",
            ),
            dict(name="**FAP Predictions**", value=get_all_predictions()),
        ],
    )

    # TODO Work on the 'get_croot_predictions' and figure out where it went
    # if (recruit.committed.lower() if recruit.committed is not None else None) not in [
    #     "signed",
    #     "enrolled",
    # ]:
    #     if (get_croot_predictions(recruit)) is not None:
    #         embed.set_footer(
    #             text=BOT_FOOTER_BOT
    #             + "\nClick the 🔮 to predict what school you think this recruit will commit to."
    #             "\nClick the 📜 to get the individual predictions for this recruit."
    #         )
    #     else:
    #         embed.set_footer(
    #             text=BOT_FOOTER_BOT
    #             + "\nClick the 🔮 to predict what school you think this recruit will commit to."
    #         )
    # else:
    #     if (get_croot_predictions(recruit)) is not None:
    #         embed.set_footer(
    #             text=BOT_FOOTER_BOT
    #             + "\nClick the 📜 to get the individual predictions for this recruit."
    #         )
    #     else:
    #         embed.set_footer(text=BOT_FOOTER_BOT)
    embed.set_footer(text=BOT_FOOTER_BOT)

    if recruit.thumbnail and not recruit.thumbnail == "/.":
        embed.set_thumbnail(url=recruit.thumbnail)
    else:
        embed.set_thumbnail(url=BOT_THUMBNAIL_URL)
    return embed


logger.info(f"{str(__name__).title()} module loaded!")
