from datetime import datetime

import discord

import objects.FAP as FAP
from objects.Schedule import HuskerSchedule
from utilities.constants import BOT_FOOTER_BOT
from utilities.constants import DT_TBA_HR, DT_TBA_MIN, DT_OBJ_FORMAT_TBA, DT_OBJ_FORMAT
from utilities.constants import TZ, BOT_DISPLAY_NAME, BOT_GITHUB_URL, BOT_ICON_URL, BOT_THUMBNAIL_URL


def build_embed(title, **kwargs):
    timestamp = datetime.now().astimezone(tz=TZ)

    if "color" in kwargs.keys():
        if "description" in kwargs.keys():
            embed = discord.Embed(title=title, description=kwargs["description"], color=kwargs["color"], timestamp=timestamp)
        else:
            embed = discord.Embed(title=title, color=kwargs["color"], timestamp=timestamp)
    else:
        if "description" in kwargs.keys():
            embed = discord.Embed(title=title, description=kwargs["description"], color=0xD00000)
        else:
            embed = discord.Embed(title=title, color=0xD00000)

    embed.set_author(name=BOT_DISPLAY_NAME, url=BOT_GITHUB_URL, icon_url=BOT_ICON_URL)

    if "footer" in kwargs.keys():
        embed.set_footer(text=kwargs["footer"])
    else:
        embed.set_footer(text=BOT_FOOTER_BOT)

    if "url" in kwargs.keys():
        embed.url = kwargs["url"]

    if "image" in kwargs.keys():
        embed.set_image(url=kwargs["image"])

    if "thumbnail" in kwargs.keys():
        embed.set_thumbnail(url=kwargs["thumbnail"])
    else:
        embed.set_thumbnail(url=BOT_THUMBNAIL_URL)

    try:
        for field in kwargs["fields"]:
            if "inline" in kwargs:
                embed.add_field(name=field[0], value=field[1], inline=kwargs["inline"])
            else:
                embed.add_field(name=field[0], value=field[1])
    except KeyError:
        pass

    return embed


def build_countdown_embed(days: int, hours: int, minutes: int, opponent, date_time: datetime, consensus, location):
    if date_time.hour == DT_TBA_HR and date_time.minute == DT_TBA_MIN:  # Place holder hour and minute to signify TBA games
        return build_embed(
            title="Countdown until...",
            inline=False,
            fields=[
                ["Opponent", opponent],
                ["Scheduled Time", date_time.strftime(DT_OBJ_FORMAT_TBA)],
                ["Location", location],
                ["Time Remaining", f"{days}"],
                ["Consensus Line", consensus if consensus else 'Line TBD']
            ]
        )
    else:
        return build_embed(
            title="Countdown until...",
            inline=False,
            fields=[
                ["Opponent", opponent],
                ["Scheduled Time", date_time.strftime(DT_OBJ_FORMAT)],
                ["Location", location],
                ["Time Remaining", f"{days} days, {hours} hours, and {minutes} minutes"],
                ["Consensus Line", consensus if consensus else 'Line TBD']
            ]
        )


def build_recruit_embed(recruit):
    def prettify_predictions():
        pretty = ""
        for item in recruit.predictions:
            pretty += f"{item}\n"
        return pretty

    def prettify_experts():
        pretty = ""
        for item in recruit.experts:
            pretty += f"{item}\n"
        return pretty

    def prettify_offers():
        pretty = ""
        for index, item in enumerate(recruit.recruit_interests):
            if index > 9:
                return pretty + f"[View remaining offers...]({recruit.recruit_interests_url})"

            pretty += f"{item.school}{' - ' + item.status if not item.status == 'None' else ''}\n"

        return pretty

    def fap_predictions():
        fap_preds = FAP.get_faps(recruit)
        if fap_preds is None:
            return "There are no predictions for this recruit."
        else:
            init_string = f"Team: Percent (Avg Confidence)"
            for p in fap_preds:
                init_string += f"\n{p['team']}: {p['percent']:.0f}% ({p['confidence']:.1f})"
            init_string += f"\nTotal Predictions: {fap_preds[0]['total']}"
            return init_string

    nl = "\n"
    embed = build_embed(
        title=f"{recruit.name}, {str(recruit.rating_stars) + '⭐ ' if recruit.rating_stars else ''}{recruit.year} {recruit.position}",
        description=f"{recruit.committed if recruit.committed is not None else ''}{': ' + recruit.committed_school if recruit.committed_school is not None else ''} {': ' + str(recruit.commitment_date.strftime('%b %d, %Y')) if recruit.commitment_date is not None else ''}",
        fields=[
            ["**Biography**", f"{recruit.city}, {recruit.state}\n"
                              f"School: {recruit.school}\n"
                              f"School Type: {recruit.school_type}\n"
                              f"Height: {recruit.height}\n"
                              f"Weight: {recruit.weight}\n"],

            ["**Social Media**", f"{'[@' + recruit.twitter + '](' + 'https://twitter.com/' + recruit.twitter + ')' if not recruit.twitter == 'N/A' else 'N/A'}"],

            ["**Highlights**", f"{'[247Sports](' + recruit.x247_highlights + ')' if recruit.x247_highlights else '247Sports N/A'}\n"
                               f"{'[Rivals](' + recruit.rivals_highlights + ')' if recruit.rivals_highlights else 'Rivals N/A'}\n"],

            ["**Recruit Info**", f"[247Sports Profile]({recruit.x247_profile})\n"
                                 f"[Rivals Profile]({recruit.rivals_profile})\n"
                                 f"Comp. Rating: {recruit.rating_numerical if recruit.rating_numerical else 'N/A'} \n"
                                 f"Nat. Ranking: [{recruit.national_ranking:,}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup"
                                 f"={recruit.school_type.replace(' ', '')})\n"
                                 f"State Ranking: [{recruit.state_ranking}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup={recruit.school_type.replace(' ', '')}&State"
                                 f"={recruit.state_abbr})\n"
                                 f"Pos. Ranking: [{recruit.position_ranking}](https://247sports.com/Season/{recruit.year}-Football/CompositeRecruitRankings/?InstitutionGroup="
                                 f"{recruit.school_type.replace(' ', '')}&Position"
                                 f"={recruit.pos_abbr})\n"
                                 f"{'All Time Ranking: [' + recruit.all_time_ranking + '](https://247sports.com/Sport/Football/AllTimeRecruitRankings/)' + nl if recruit.all_time_ranking else ''}"
                                 f"{'Early Enrollee' + nl if recruit.early_enrollee else ''}"
                                 f"{'Early Signee' + nl if recruit.early_signee else ''}"
                                 f"{'Walk-On' + nl if recruit.walk_on else ''}"],

            ["**Expert Averages**", f"{prettify_predictions() if recruit.predictions else 'N/A'}"],

            ["**Lead Expert Picks**", f"{prettify_experts() if recruit.experts else 'N/A'}"],

            ["**Offers**", f"{prettify_offers() if recruit.recruit_interests else 'N/A'}"],

            ["**FAP Predictions**", f"{fap_predictions()}"]
        ]
    )

    if (recruit.committed.lower() if recruit.committed is not None else None) not in ['signed', 'enrolled']:
        if (FAP.get_croot_predictions(recruit)) is not None:
            embed.set_footer(text=BOT_FOOTER_BOT + "\nClick the 🔮 to predict what school you think this recruit will commit to."
                                                   "\nClick the 📜 to get the inividual predictions for this recruit.")
        else:
            embed.set_footer(text=BOT_FOOTER_BOT + "\nClick the 🔮 to predict what school you think this recruit will commit to.")
    else:
        if (FAP.get_croot_predictions(recruit)) is not None:
            embed.set_footer(text=BOT_FOOTER_BOT + "\nClick the 📜 to get the inividual predictions for this recruit.")
        else:
            embed.set_footer(text=BOT_FOOTER_BOT)

    if not recruit.thumbnail == "/.":
        embed.set_thumbnail(url=recruit.thumbnail)
    return embed


# def build_schedule_embed(year, **kwargs):
#     scheduled_games, season_stats = HuskerSchedule(year=year, sport=kwargs["sport"])
#
#     arrow = "» "
#     _nl = "\n"
#
#     embed = build_embed(
#         title=f"Nebraska's {year} Schedule ({season_stats.wins} - {season_stats.losses})",
#     )
#
#     if "week" in kwargs:
#         game = scheduled_games[int(kwargs["week"]) - 1]
#
#         value_string = f"{arrow + ' ' + game.outcome + _nl if not game.outcome == '' else ''}" \
#                        f"{arrow}{'B1G Game' if game.opponent.conference == 'Big Ten' else 'Non-Con Game'}{_nl}" \
#                        f"{arrow}{game.opponent.date_time}{_nl}" \
#                        f"{arrow}{game.location}"
#
#         embed.add_field(
#             name=f"**#{game.week}: {game.opponent.name}**",
#             value=value_string
#         )
#
#         embed.set_image(url=game.opponent.icon)
#     else:
#         for index, game in enumerate(scheduled_games):
#             value_string = f"{arrow + ' ' + game.outcome + _nl if not game.outcome == '' else ''}" \
#                            f"{arrow}{'B1G Game' if game.opponent.conference == 'Big Ten' else 'Non-Con Game'}{_nl}" \
#                            f"{arrow}{game.opponent.date_time}{_nl}" \
#                            f"{arrow}{game.location}"
#
#             embed.add_field(
#                 name=f"**#{game.week}: {game.opponent.name}**",
#                 value=value_string
#             )
#
#     return embed
