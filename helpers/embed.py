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
                inline=field["inline"],
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
            dict(name="Message", value=text, inline=False),
            dict(
                name="Tweet URL",
                value=f"https://twitter.com/{username}/status/{tweet_id}",
                inline=False,
            ),
        ],
    )

    if urls:
        for url in urls["urls"]:
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
                inline=False,
            )

    if medias:
        for index, item in enumerate(medias):
            embed.add_field(
                name="Embeded Image",
                value=discordURLFormatter(f"Image #{index+1}", item.url),
                inline=False,
            )

    if quotes:
        for item in quotes:
            embed.add_field(
                name="Quoted Tweet",
                value=item.text,
                inline=False,
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

# def build_countdown_embed(
#     days: int,
#     hours: int,
#     minutes: int,
#     opponent,
#     thumbnail,
#     date_time: datetime,
#     consensus,
#     location,
# ):
#     if (
#         date_time.hour == DT_TBA_HR and date_time.minute == DT_TBA_MIN
#     ):  # Place holder hour and minute to signify TBA games
#         return build_embed(
#             title="Countdown until...",
#             inline=False,
#             thumbnail=thumbnail,
#             fields=[
#                 ["Opponent", opponent],
#                 ["Scheduled Time", date_time.strftime(DT_OBJ_FORMAT_TBA)],
#                 ["Location", location],
#                 ["Time Remaining", f"{days}"],
#                 ["Betting Info", consensus if consensus else "Line TBD"],
#             ],
#         )
#     else:
#         return build_embed(
#             title="Countdown until...",
#             inline=False,
#             thumbnail=thumbnail,
#             fields=[
#                 ["Opponent", opponent],
#                 ["Scheduled Time", date_time.strftime(DT_OBJ_FORMAT)],
#                 ["Location", location],
#                 [
#                     "Time Remaining",
#                     f"{days} days, {hours} hours, and {minutes} minutes",
#                 ],
#                 ["Betting Info", consensus if consensus else "Line TBD"],
#             ],
#         )
#
#
# def build_recruit_embed(recruit):
#     def prettify_predictions():
#         pretty = ""
#         for item in recruit.cb_predictions:
#             pretty += f"{item}\n"
#         return pretty
#
#     def prettify_experts():
#         pretty = ""
#         for item in recruit.cb_experts:
#             pretty += f"{item}\n"
#         return pretty
#
#     def prettify_offers():
#         pretty = ""
#         for index, item in enumerate(recruit.recruit_interests):
#             if index > 9:
#                 return (
#                     pretty
#                     + f"[View remaining offers...]({recruit.recruit_interests_url})"
#                 )
#
#             pretty += f"{item.school}{' - ' + item.status if not item.status == 'None' else ''}\n"
#
#         return pretty
#
#     def fap_predictions():
#         fap_preds = FAP.get_faps(recruit)
#         if fap_preds is None:
#             return "There are no predictions for this recruit."
#         else:
#             init_string = f"Team: Percent (Avg Confidence)"
#             for p in fap_preds:
#                 init_string += (
#                     f"\n{p['team']}: {p['percent']:.0f}% ({p['confidence']:.1f})"
#                 )
#             init_string += f"\nTotal Predictions: {fap_preds[0]['total']}"
#             return init_string
#
#     nl = "\n"
#     embed = build_embed(
#         title=f"{str(recruit.rating_stars) + '⭐ ' if recruit.rating_stars else ''}{recruit.year} {recruit.position}, {recruit.name}",
#         description=f"{recruit.committed if recruit.committed is not None else ''}"
#         f"{': ' + recruit.committed_school if recruit.committed_school is not None else ''} "
#         f"{': ' + str(datetime.strptime(recruit.commitment_date, DT_STR_RECRUIT)) if recruit.commitment_date is not None else ''}",
#         fields=[
#             [
#                 "**Biography**",
#                 f"{recruit.city}, {recruit.state}\n"
#                 f"School: {recruit.school}\n"
#                 f"School Type: {recruit.school_type}\n"
#                 f"Height: {recruit.height}\n"
#                 f"Weight: {recruit.weight}\n",
#             ],
#             [
#                 "**Social Media**",
#                 f"{'[@' + recruit.twitter + '](' + 'https://twitter.com/' + recruit.twitter + ')' if not recruit.twitter == 'N/A' else 'N/A'}",
#             ],
#             [
#                 "**Highlights**",
#                 f"{'[247Sports](' + recruit._247_highlights + ')' if recruit._247_highlights else '247Sports N/A'}",
#             ],
#             [
#                 "**Recruit Info**",
#                 f"[247Sports Profile]({recruit._247_profile})\n"
#                 f"Comp. Rating: {recruit.rating_numerical if recruit.rating_numerical else 'N/A'} \n"
#                 f"Nat. Ranking: [{recruit.ranking_national:,}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup"
#                 f"={recruit.school_type.replace(' ', '')})\n"
#                 f"State Ranking: [{recruit.ranking_state}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup={recruit.school_type.replace(' ', '')}&State"
#                 f"={recruit.state_abbr})\n"
#                 f"Pos. Ranking: [{recruit.ranking_position}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup="
#                 f"{recruit.school_type.replace(' ', '')}&Position={recruit.position})\n"
#                 f"{'All Time Ranking: [' + recruit.ranking_all_time + '](https://247sports.com/Sport/Football/AllTimeRecruitRankings/)' + nl if recruit.ranking_all_time else ''}"
#                 f"{'Early Enrollee' + nl if recruit.early_enrollee else ''}"
#                 f"{'Early Signee' + nl if recruit.early_signee else ''}"
#                 f"{'Walk-On' + nl if recruit.walk_on else ''}",
#             ],
#             [
#                 "**Expert Averages**",
#                 f"{prettify_predictions() if recruit.cb_predictions else 'N/A'}",
#             ],
#             [
#                 "**Lead Expert Picks**",
#                 f"{prettify_experts() if recruit.cb_experts else 'N/A'}",
#             ],
#             [
#                 "**Offers**",
#                 f"{prettify_offers() if recruit.recruit_interests else 'N/A'}",
#             ],
#             ["**FAP Predictions**", f"{fap_predictions()}"],
#         ],
#     )
#
#     if (recruit.committed.lower() if recruit.committed is not None else None) not in [
#         "signed",
#         "enrolled",
#     ]:
#         if (FAP.get_croot_predictions(recruit)) is not None:
#             embed.set_footer(
#                 text=BOT_FOOTER_BOT
#                 + "\nClick the 🔮 to predict what school you think this recruit will commit to."
#                 "\nClick the 📜 to get the individual predictions for this recruit."
#             )
#         else:
#             embed.set_footer(
#                 text=BOT_FOOTER_BOT
#                 + "\nClick the 🔮 to predict what school you think this recruit will commit to."
#             )
#     else:
#         if (FAP.get_croot_predictions(recruit)) is not None:
#             embed.set_footer(
#                 text=BOT_FOOTER_BOT
#                 + "\nClick the 📜 to get the individual predictions for this recruit."
#             )
#         else:
#             embed.set_footer(text=BOT_FOOTER_BOT)
#
#     if not recruit.thumbnail == "/.":
#         embed.set_thumbnail(url=recruit.thumbnail)
#     return embed
#
#
# def build_schedule_embed(year, **kwargs):
#     scheduled_games, season_stats = HuskerSchedule(year=year, sport=kwargs["sport"])
#
#     arrow = "» "
#     new_line_char = "\n"
#     fields = []
#
#     for game in scheduled_games:
#         field_value = (
#             f"{arrow + game.outcome + new_line_char if not game.outcome == '' else ''}"
#             f"{arrow}{game.game_date_time.strftime(DT_OBJ_FORMAT) if not game.game_date_time.hour == 21 else game.game_date_time.strftime(DT_OBJ_FORMAT_TBA)}{new_line_char}"
#             f"{arrow}{game.location}"
#         )
#
#         fields.append(
#             [
#                 f"**Week {game.week}: {game.opponent} ({'Home' if game.home else 'Away'}) **",
#                 field_value,
#             ]
#         )
#
#     embed = build_embed(
#         title=f"Nebraska's {year} Schedule ({season_stats.wins} - {season_stats.losses})",
#         inline=False,
#         fields=fields,
#     )
#
#     return embed
#
#
# def return_schedule_embeds(year, **kwargs):
#     scheduled_games, season_stats = HuskerSchedule(year=year, sport=kwargs["sport"])
#
#     new_line_char = "\n"
#     embeds = []
#
#     for game in scheduled_games:
#         embeds.append(
#             build_embed(
#                 title=f"{game.opponent.title()}",
#                 description=f"Nebraska's {year}'s Record: {season_stats.wins} - {season_stats.losses}",
#                 inline=False,
#                 thumbnail=game.icon,
#                 fields=[
#                     [
#                         "Opponent",
#                         f"{game.ranking + ' ' if game.ranking else ''}{game.opponent}",
#                     ],
#                     ["Conference Game", "Yes" if game.conference else "No"],
#                     [
#                         "Date/Time",
#                         f"{game.game_date_time.strftime(DT_OBJ_FORMAT) if not game.game_date_time.hour == 21 else game.game_date_time.strftime(DT_OBJ_FORMAT_TBA)}{new_line_char}",
#                     ],
#                     ["Location", game.location],
#                     ["Outcome", game.outcome if game.outcome else "TBD"],
#                 ],
#             )
#         )
#
#     return embeds
