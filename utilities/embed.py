# TODO
# * Update and modernize
# TODO
# from datetime import datetime
#
# import discord
# import validators
#
# import commands.recruiting as FAP
# from objects.Schedule import HuskerSchedule
# from utilities.constants import (
#     BOT_DISPLAY_NAME,
#     BOT_FOOTER_BOT,
#     BOT_GITHUB_URL,
#     BOT_ICON_URL,
#     BOT_THUMBNAIL_URL,
#     DT_OBJ_FORMAT,
#     DT_OBJ_FORMAT_TBA,
#     DT_STR_RECRUIT,
#     DT_TBA_HR,
#     DT_TBA_MIN,
#     TZ,
# )
#
#
# class EmbedType:
#     rich = "rich"
#     image = "image"
#     video = "video"
#     gifv = "gifv"
#     article = "article"
#     link = "link"
#
#
# def build_embed(**kwargs):
#     title_limit = name_limit = 256
#     desc_limit = 4096
#     fields_limit = 25
#     value_limit = 1024
#     footer_limit = 2048
#     # embed_limit = 6000
#
#     if kwargs.get("color", False):
#         embed = discord.Embed(
#             timestamp=datetime.now().astimezone(tz=TZ), color=kwargs.get("color")
#         )
#     else:
#         embed = discord.Embed(
#             timestamp=datetime.now().astimezone(tz=TZ), color=0xD00000
#         )
#
#     if kwargs.get("author", False) is not None:
#         embed.set_author(
#             name=BOT_DISPLAY_NAME, url=BOT_GITHUB_URL, icon_url=BOT_ICON_URL
#         )
#
#     if kwargs.get("description", False):
#         embed.description = kwargs.get("description")[:desc_limit]
#
#     if kwargs.get("title", False):
#         embed.title = kwargs.get("title")[:title_limit]
#
#     if kwargs.get("url", False) and validators.url(kwargs.get("url")):
#         embed.url = kwargs.get("url")
#
#     if kwargs.get("type", False):
#         embed.type = kwargs.get("type")
#     else:
#         embed.type = EmbedType.rich
#
#     if kwargs.get("footer", False):
#         embed.set_footer(
#             text=kwargs.get("footer")[:footer_limit], icon_url=BOT_ICON_URL
#         )
#
#     if kwargs.get("image", False) and validators.url(kwargs.get("image")):
#         if kwargs.get("image") is not None:
#             embed.set_image(url=kwargs["image"])
#
#     if kwargs.get("thumbnail", False):
#         embed.set_thumbnail(url=kwargs.get("thumbnail"))
#     else:
#         if kwargs.get("thumbnail") is not None:
#             embed.set_thumbnail(url=BOT_THUMBNAIL_URL)
#
#     if kwargs.get("fields", False):
#         for index, field in enumerate(kwargs["fields"]):
#             if index >= fields_limit:
#                 break
#
#             if kwargs.get("inline", False):
#                 embed.add_field(
#                     name=str(field[0])[:name_limit],
#                     value=str(field[1])[:value_limit],
#                     inline=kwargs["inline"],
#                 )
#             else:
#                 embed.add_field(
#                     name=str(field[0])[:name_limit],
#                     value=str(field[1])[:value_limit],
#                     inline=False,
#                 )
#
#     return embed
#
#
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
