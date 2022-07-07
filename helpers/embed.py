import inspect
import logging
from datetime import datetime
from typing import Union, Optional

import discord
import validators
from cfbd import ApiClient, GamesApi, Game, TeamRecord

from helpers.constants import (
    BOT_FOOTER_BOT,
    BOT_ICON_URL,
    BOT_THUMBNAIL_URL,
    CFBD_CONFIG,
    DESC_LIMIT,
    DT_STR_RECRUIT,
    DT_TWEET_FORMAT,
    EMBED_MAX,
    FIELDS_LIMIT,
    FIELD_NAME_LIMIT,
    FIELD_VALUE_LIMIT,
    FOOTER_LIMIT,
    NAME_LIMIT,
    TITLE_LIMIT,
    TZ,
    DT_CFBD_GAMES,
    DT_CFBD_GAMES_DISPLAY,
)
from helpers.misc import discordURLFormatter, getModuleMethod
from helpers.mysql import processMySQL, sqlGetCrootPredictions
from objects.Bets_Stats_Schedule import BigTenTeams, getHuskerOpponent, buildTeam
from objects.Exceptions import BettingException

logger = logging.getLogger(__name__)

__all__: list[str] = [
    "buildEmbed",
    "buildRecruitEmbed",
    "buildTweetEmbed",
    "collectScheduleEmbeds",
]


def buildEmbed(title: Optional[str], **kwargs) -> Union[discord.Embed, None]:
    module, method = getModuleMethod(inspect.stack())
    logger.debug(f"Creating a normal embed from [{module}-{method}]")

    dtNow = datetime.now().astimezone(tz=TZ)

    if "color" in kwargs.keys():
        if "description" in kwargs.keys():
            e = discord.Embed(
                title=title[:TITLE_LIMIT],
                description=kwargs["description"][:DESC_LIMIT],
                color=discord.Color.from_str(kwargs["color"]),
                timestamp=dtNow,
            )
        else:
            e = discord.Embed(
                title=title[:TITLE_LIMIT],
                color=discord.Color.from_str(kwargs["color"]),
                timestamp=dtNow,
            )
    else:
        if "description" in kwargs.keys():
            e = discord.Embed(
                title=title[:TITLE_LIMIT],
                description=kwargs["description"][:DESC_LIMIT],
                color=0xD00000,
            )
        else:
            e = discord.Embed(title=title[:TITLE_LIMIT], color=0xD00000)

    if "footer" in kwargs.keys():
        e.set_footer(text=kwargs.get("footer")[:FOOTER_LIMIT], icon_url=BOT_ICON_URL)
    else:
        e.set_footer(
            text=BOT_FOOTER_BOT[:FOOTER_LIMIT],
            icon_url=BOT_ICON_URL,
        )

    if "image" in kwargs.keys() and validators.url(kwargs.get("image")):
        e.set_image(url=kwargs.get("image"))

    if "author" in kwargs.keys():
        e.set_author(
            name=kwargs.get("author")[:NAME_LIMIT],
            url="",
            icon_url=kwargs.get("icon_url", ""),
        )

    if "thumbnail" in kwargs.keys() and validators.url(kwargs.get("thumbnail")):
        e.set_thumbnail(url=kwargs.get("thumbnail"))
    else:
        e.set_thumbnail(url=BOT_THUMBNAIL_URL)

    if "fields" in kwargs.keys():
        for index, field in enumerate(kwargs.get("fields")):
            if index == FIELDS_LIMIT:
                break

            e.add_field(
                name=field["name"][:FIELD_NAME_LIMIT],
                value=field["value"][:FIELD_VALUE_LIMIT],
                inline=field.get("inline", False),
            )
    if len(e) > EMBED_MAX:
        logger.exception("Embed is too big!", exc_info=True)
        raise
    else:
        logger.debug(f"Returning a normal embed from [{module}-{method}]")
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
    b16: bool = False,
) -> discord.Embed:
    module, method = getModuleMethod(inspect.stack())
    logger.info(f"Creating a tweet embed from [{module}-{method}]")

    if b16 and medias:
        logger.info(f"Creating a Block 16 embed from [{module}-{method}]")
        return buildEmbed(
            author=f"{name} (@{username})",
            title="Block 16 Tweet",
            description=text if text else "",
            image=medias[0].url,
            fields=[
                dict(
                    name="Link to Tweet",
                    value=f"https://twitter.com/{username}/status/{tweet_id}",
                )
            ],
        )
    elif b16:
        logger.info(f"Creating a Block 16 embed from [{module}-{method}]")
        return buildEmbed(
            author=f"{name} (@{username})",
            title="Block 16 Tweet",
            description=text if text else "",
            fields=[
                dict(
                    name="Link to Tweet",
                    value=f"https://twitter.com/{username}/status/{tweet_id}",
                )
            ],
        )

    embed = buildEmbed(
        title="",
        description=f"Followers: {author_metrics['followers_count']} • Tweets: {author_metrics['tweet_count']}",
        fields=[
            dict(
                name="Message",
                value=text,
            ),
            dict(
                name="Link to Tweet",
                value=f"https://twitter.com/{username}/status/{tweet_id}",
            ),
        ],
    )
    if urls.get("urls", None):  # TODO KeyError is raising
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
                name="Embedded URL",
                value=discordURLFormatter(
                    display_text=url["title"], url=url["expanded_url"]
                ),
            )

    if medias:
        for index, item in enumerate(medias):
            if index == 0 and item.get("url", False):
                embed.set_image(url=item.url)
            embed.add_field(
                name="Embedded Image",
                value=discordURLFormatter(f"Image #{index + 1}", item.url),
            )

    if quotes:
        for item in quotes:
            embed.add_field(
                name="Quoted Tweet",
                value=item.text,
            )

    embed.set_author(
        name=f"{name}{' ☑️' if verified else ' '}(@{username})",
        url=f"https://twitter.com/{username}",
        icon_url=profile_image_url,
    )
    embed.set_footer(
        text=f"Sent via {source} at {tweet_created_at.strftime(DT_TWEET_FORMAT)}"[  # • Retweets: {tweet_metrics['retweet_count']} • Replies: {tweet_metrics['reply_count']} • Likes: {tweet_metrics['like_count']} • Quotes: {tweet_metrics['quote_count']}"[
            :FOOTER_LIMIT
        ],
    )
    embed.set_thumbnail(url=profile_image_url)

    logger.info(f"Finished tweet embed from [{module}-{method}]")
    return embed


def collectScheduleEmbeds(year: int) -> list[discord.Embed]:
    module, method = getModuleMethod(inspect.stack())
    logger.info(f"Attempting to create schedule embeds from [{module}-{method}]")

    embeds: list[Optional[discord.Embed]] = []

    games_api: GamesApi = GamesApi(ApiClient(CFBD_CONFIG))
    games: list[Game] = games_api.get_games(
        year=year, team=BigTenTeams.Nebraska.lower(), season_type="both"
    )
    records: Union[list[TeamRecord], TeamRecord] = games_api.get_team_records(
        team=BigTenTeams.Nebraska.value, year=year
    )

    try:
        records = records[0]
        records_str: str = f"Nebraska's {year} Record: {records.total['wins']} - {records.total['losses']}"  # noqa
    except IndexError:
        records_str = ""

    for index, game in enumerate(games):
        logger.info(
            f"Trying to create game embed for: {game.home_team}, {game.away_team}"
        )

        title_str: str = f"{year} Game #{index + 1}: {game.home_team.title()} vs. {game.away_team.title()}"

        datetime_str = (
            datetime.strptime(game.start_date, DT_CFBD_GAMES)
            .astimezone(tz=TZ)
            .strftime(DT_CFBD_GAMES_DISPLAY)
        )

        if game.away_points is None and game.home_points is None:
            outcome_str: str = "TBD"
        else:
            outcome_max_len: int = 17  # arbitrary
            outcome_home_len: int = outcome_max_len - (
                len(game.home_team) + len(str(game.home_points))
            )
            outcome_away_len: int = outcome_max_len - (
                len(game.away_team) + len(str(game.away_points))
            )
            outcome_str = f"```\n{game.home_team}{' ':<{outcome_home_len}}{game.home_points}\n{game.away_team}{' ':<{outcome_away_len}}{game.away_points}\n```"

        if game.home_post_win_prob is None and game.away_post_win_prob is None:
            probability_str: str = "TBD"
        else:
            probability_str: str = f"```\n{game.home_team} {game.home_post_win_prob * 100:#.2f}%\n{game.away_team} {game.away_post_win_prob * 100:#.2f}%\n```"

        if game.excitement_index is None:
            excitement_str: str = "TBD"
        else:
            excitement_str = f"{game.excitement_index:#.4f}"

        try:  # Some opponents don't have records on CFBD
            opponent_info = buildTeam(getHuskerOpponent(game)["id"])
        except BettingException:
            embeds.append(
                buildEmbed(
                    title=title_str,
                    description=records_str,
                    fields=[
                        dict(
                            name="Date/Time",
                            value=datetime_str,
                        ),
                        dict(name="Location", value=game.venue),
                        dict(name="Outcome", value=outcome_str),
                        dict(name="Win Probability", value=probability_str),
                        dict(
                            name="Excitement Index",
                            value=excitement_str,
                        ),
                    ],
                )
            )
            continue

        if opponent_info.school_name.lower() == game.away_team.lower():
            away_alt: str = opponent_info.alt_name
            home_alt: str = "NEB"
        elif opponent_info.school_name.lower() == game.home_team.lower():
            away_alt = "NEB"
            home_alt = opponent_info.alt_name
        else:
            away_alt = "____"
            home_alt = "____"

        if game.away_line_scores is None and game.home_line_scores is None:
            away_boxes: list[int] = [0, 0, 0, 0]
            home_boxes: list[int] = [0, 0, 0, 0]
        else:
            away_boxes = game.away_line_scores
            home_boxes = game.home_line_scores

        if sum(away_boxes) + sum(home_boxes) == 0:
            boxscore_str: str = "TBD"
        else:
            boxscore_str = (
                f"```\n"
                f" TM | Q1 | Q2 | Q3 | Q4 | FIN \n"
                f" {home_alt[:3]:<3}| {home_boxes[0]:<3}| {home_boxes[1]:<3}| {home_boxes[2]:<3}| {home_boxes[3]:<3}| {game.home_points:<3}\n"
                f" {away_alt[:3]:<3}| {away_boxes[0]:<3}| {away_boxes[1]:<3}| {away_boxes[2]:<3}| {away_boxes[3]:<3}| {game.away_points:<3}\n"
                f"```"
            )
        if (
            game.home_pregame_elo is None
            and game.home_postgame_elo is None
            and game.away_pregame_elo is None
            and game.away_postgame_elo is None
        ):
            elo_str: str = "TBD"
        elif (
            game.home_pregame_elo
            and game.home_postgame_elo is None
            and game.away_pregame_elo
            and game.away_postgame_elo is None
        ):
            elo_str = f"```\n{game.home_team} {game.home_pregame_elo:,}\n{game.away_team} {game.away_pregame_elo:,}\n```"
        else:
            elo_str = f"```\n{game.home_team} {game.home_pregame_elo:,} -> {game.home_postgame_elo:,}\n{game.away_team} {game.away_pregame_elo:,} -> {game.away_postgame_elo:,}\n```"

        embeds.append(
            buildEmbed(
                title=title_str,
                description=records_str,  # noqa
                thumbnail=opponent_info.logo,
                fields=[
                    dict(
                        name="Date/Time",
                        value=datetime_str,
                    ),
                    dict(
                        name="Conference/Division",
                        value=f"{opponent_info.conference}/{opponent_info.division}",
                    ),
                    dict(name="Location", value=game.venue),
                    dict(name="Outcome", value=outcome_str),
                    dict(name="Boxscore", value=boxscore_str),
                    dict(name="Win Probability", value=probability_str),
                    dict(name="Elo Rating", value=elo_str),
                    dict(
                        name="Excitement Index",
                        value=excitement_str,
                    ),
                ],
            )
        )

    logger.info(f"Returning schedule embeds from [{module}-{method}]")
    return embeds


def buildRecruitEmbed(recruit) -> discord.Embed:
    module, method = getModuleMethod(inspect.stack())
    logger.info(f"Creating a recruit embed from [{module}-{method}]")

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

    def prettify_predictions() -> str:
        pretty = ""
        for item in recruit.cb_predictions:
            pretty += f"{item}\n"
        return pretty

    def prettify_experts() -> str:
        pretty = ""
        for item in recruit.cb_experts:
            pretty += f"{item}\n"
        return pretty

    def prettify_offers() -> str:
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

    embed.set_footer(text=BOT_FOOTER_BOT)

    if recruit.thumbnail and not recruit.thumbnail == "/.":
        embed.set_thumbnail(url=recruit.thumbnail)
    else:
        embed.set_thumbnail(url=BOT_THUMBNAIL_URL)

    logger.info(f"Creating a recruit embed from [{module}-{method}]")
    return embed


logger.info(f"{str(__name__).title()} module loaded!")
