from datetime import datetime

import discord

from utils.consts import tz


def build_image_embed(title, image):
    embed = discord.Embed(title=title, color=0xD00000)
    embed.set_author(name="Bot Frost", url="https://github.com/refekt/Husker-Bot", icon_url="https://i.imgur.com/Ah3x5NA.png")
    embed.set_footer(text="Created by Bot Frost")
    embed.set_image(url=image)
    return embed


def build_embed(title, **kwargs):
    timestamp = datetime.utcnow().astimezone(tz=tz)

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

    embed.set_author(name="Bot Frost", url="https://github.com/refekt/Husker-Bot", icon_url="https://i.imgur.com/Ah3x5NA.png")
    embed.set_footer(text=f"Embed created on {timestamp.strftime('%a %b %e, %Y at %I:%M %p')}")

    if "image" in kwargs.keys():
        embed.set_image(url=kwargs["image"])

    if "thumbnail" in kwargs.keys():
        embed.set_thumbnail(url=kwargs["thumbnail"])
    else:
        embed.set_thumbnail(url="https://ucomm.unl.edu/images/brand-book/Our-marks/nebraska-n.jpg")

    try:
        for field in kwargs["fields"]:
            if "inline" in kwargs:
                embed.add_field(name=field[0], value=field[1], inline=kwargs["inline"])
            else:
                embed.add_field(name=field[0], value=field[1])
    except KeyError:
        pass

    return embed


def build_recruit_embed(rec):  # rec == recruit
    def predictions_pretty():
        pretty = ""
        for item in rec.predictions:
            pretty += f"{item}\n"
        return pretty

    def offers_pretty():
        pretty = ""
        for index, item in enumerate(rec.recruit_interests):
            if index > 9:
                return pretty + f"[View remaining offers...]({rec.recruit_interests_url})"

            pretty += f"{item.school}{' - ' + item.status if not item.status == 'None' else ''}\n"

        return pretty

    nl = "\n"
    embed = build_embed(
        title=f"{rec.name}, {str(rec.rating_stars) + '⭐ ' if rec.rating_stars else ''}{rec.year} {rec.position}",
        description=f"{rec.committed if rec.committed is not None else ''} {': ' + rec.committed_school if rec.committed_school is not None else ''} {': ' + str(rec.commitment_date.strftime('%b %d, %Y')) if rec.commitment_date is not None else ''}",
        fields=[
            ["**Biography**", f"{rec.city}, {rec.state}\n"
                              f"School: {rec.school}\n"
                              f"School Type: {rec.school_type}\n"
                              f"Height: {rec.height}\n"
                              f"Weight: {rec.weight}\n"],

            ["**Recruit Info**", f"[247Sports Profile]({rec.x247_profile})\n"
                                 f"[Rivals Profile]({rec.rivals_profile})\n"
                                 f"Comp. Rating: {rec.rating_numerical if rec.rating_numerical else 'N/A'} \n"
                                 f"Nat. Ranking: [{rec.national_ranking:,}](https://247sports.com/Season/{rec.year}-Football/CompositeRecruitRankings/?InstitutionGroup"
                                 f"={rec.school_type.replace(' ', '')})\n"
                                 f"State Ranking: [{rec.state_ranking}](https://247sports.com/Season/{rec.year}-Football/CompositeRecruitRankings/?InstitutionGroup={rec.school_type.replace(' ', '')}&State"
                                 f"={rec.state_abbr})\n"
                                 f"Pos. Ranking: [{rec.position_ranking}](https://247sports.com/Season/{rec.year}-Football/CompositeRecruitRankings/?InstitutionGroup="
                                 f"{rec.school_type.replace(' ', '')}&Position"
                                 f"={rec.pos_abbr})\n"
                                 f"{'All Time Ranking: [' + rec.all_time_ranking + '](https://247sports.com/Sport/Football/AllTimeRecruitRankings/)' + nl if rec.all_time_ranking else ''}"
                                 f"{'Early Enrollee' + nl if rec.early_enrollee else ''}"
                                 f"{'Early Signee' + nl if rec.early_signee else ''}"
                                 f"{'Walk-On' + nl if rec.walk_on else ''}"],

            ["**Highlights**", f"{'[247Sports](' + rec.x247_highlights + ')' if rec.x247_highlights else '247Sports N/A'}\n"
                               f"{'[Rivals](' + rec.rivals_highlights + ')' if rec.rivals_highlights else 'Rivals N/A'}\n"],

            ["**Crystal Balls**", f"{predictions_pretty() if rec.predictions else 'N/A'}"],

            ["**Offers**", f"{offers_pretty() if rec.recruit_interests else 'N/A'}"],

            ["**Social Media**", f"{'[@' + rec.twitter + '](' + 'https://twitter.com/' + rec.twitter + ')' if not rec.twitter == 'N/A' else 'N/A'}"]
        ]
    )
    if not rec.thumbnail == "/.":
        embed.set_thumbnail(url=rec.thumbnail)
    return embed