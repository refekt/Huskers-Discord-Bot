import json
import logging
import re
from datetime import datetime
from typing import Union, Any

import discord.ext.commands
import requests
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import commands

from helpers.constants import (
    CROOT_SEARCH_LIMIT,
    DT_FAP_RECRUIT,
    GUILD_PROD,
    HEADERS,
    RECRUIT_STATES,
)
from helpers.embed import buildEmbed, buildRecruitEmbed
from helpers.mysql import (
    processMySQL,
    sqlGetIndividualPrediction,
    sqlGetPrediction,
    sqlInsertPrediction,
    sqlTeamIDs,
)
from objects.Exceptions import RecruitException
from objects.Recruits import RecruitInterest, Recruit

logger = logging.getLogger(__name__)

croot_search = []
prediction_search = []
search_reactions = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4}

CURRENT_CLASS = datetime.now().year
NO_MORE_PREDS = datetime.now().year

__all__ = [""]


class UserPrediction:
    def __init__(
        self,
        school: Any,
        confidence: Any,
    ) -> None:
        self.school: discord.ui.TextInput = school
        self.confidence: discord.ui.Select = confidence


user_prediction: UserPrediction = UserPrediction(None, None)


class RecruitListView(discord.ui.View):
    """
    The View for each search button 1-5
    """

    def __init__(self, recruit_search: list[Recruit]) -> None:
        super().__init__()
        self.croot_search: list[Recruit] = recruit_search

        for index, reaction in enumerate(search_reactions):
            self.add_item(
                discord.ui.Button(
                    label=reaction,
                    custom_id=f"search_reaction_{index}",
                    style=discord.ButtonStyle.gray,
                )
            )
        pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await interaction.response.defer()

        reaction_pressed = int(interaction.data["custom_id"][-1])

        logger.info(f"Croot-bot search button #{reaction_pressed + 1} pressed")

        embed = buildRecruitEmbed(croot_search[reaction_pressed])
        view = createPredictionView(croot_search[reaction_pressed])

        logger.info("Sending a new recruit embed")
        await interaction.edit_original_message(embed=embed, view=view)

        return True


class PredictionTeamModal(discord.ui.Modal, title="School Prediction"):
    """
    The Modal for receiving text input to search a school
    """

    def __init__(self, recruit: Recruit) -> None:
        super().__init__()
        self.recruit: Recruit = recruit

    prediction_school = discord.ui.TextInput(label="School Prediction")
    prediction_confidence = discord.ui.TextInput(
        label="Confidence in prediction from 1 (low) to 10 (high)"[:44]
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        logger.info("Prediction modal initiated")
        await interaction.response.defer(ephemeral=True)

        global user_prediction
        user_prediction.school = self.prediction_school
        user_prediction.confidence = self.prediction_confidence
        self.stop()

        logger.info("Confirming if recruit is already committed to a school")
        formatted_team_list = [team.lower() for team in get_teams()]
        if user_prediction.school.value.lower() in formatted_team_list:
            teamm_index = formatted_team_list.index(
                user_prediction.school.value.lower()
            )
            team_prediction = get_teams()[teamm_index]

            if self.recruit.committed_school == team_prediction:
                raise RecruitException(
                    f"{self.recruit.name} is already committed to {self.recruit.committed_school}!"
                )

        else:
            raise RecruitException(
                "Your team choice was not a valid team. Please try again!"
            )

        logger.info("Inserting prediction")
        processMySQL(
            query=sqlInsertPrediction,
            values=(
                interaction.user.name,
                interaction.user.id,
                self.recruit.name,
                self.recruit.twofourseven_profile,
                self.recruit.year,
                user_prediction.school.value,
                int(user_prediction.confidence.value),
            ),
        )

        await interaction.followup.send(
            f"Your prediction of [{self.recruit.name}] to [{str(user_prediction.school.value).capitalize()}] with a [{user_prediction.confidence}] level has been logged!",
            ephemeral=True,
        )
        logger.info("Prediction was recorded!")


class PredictionView(discord.ui.View):
    """
    The View to manage submitting and retrieving predictions
    """

    def __init__(self, recruit: Recruit) -> None:
        super().__init__()
        self.recruit = recruit

    @discord.ui.button(label="🔮", disabled=True)
    async def crystal_ball(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        logger.info("Starting a crystal ball prediction")

        if (
            self.recruit.committed.lower()
            if self.recruit.committed is not None
            else None
        ) in [
            "signed",
            "enrolled",
        ]:
            raise RecruitException(
                "You cannot make predictions on recruits that have been signed or have enrolled in their school.",
            )

        if self.recruit.year < NO_MORE_PREDS:
            raise RecruitException(
                f"You cannot make predictions on recruits from before the [{NO_MORE_PREDS}] class. [{self.recruit.name}] was in the [{self.recruit.year}] recruiting class.",
            )

        logger.info("Collecting team and confidence predictions")
        modal = PredictionTeamModal(self.recruit)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @discord.ui.button(label="📜", disabled=True)
    async def scroll(self, interaction: discord.Interaction, button: discord.Button):
        logger.info(f"Retrieving predictions for {self.recruit.name}...")
        await interaction.response.defer()

        individual_preds = processMySQL(
            query=sqlGetIndividualPrediction,
            fetch="all",
            values=(self.recruit.twofourseven_profile,),
        )
        if individual_preds is None:
            raise RecruitException("This recruit has no predictions.")

        logger.info(f"Compilining {len(individual_preds)} predictions")
        predictions = []
        for index, prediction in enumerate(individual_preds):
            try:
                prediction_user = interaction.guild.get_member(prediction["user_id"])
                prediction_user = prediction_user.display_name
            except:  # noqa
                prediction_user = prediction["user"]

            if prediction_user is None:
                prediction_user = prediction["user"]

            prediction_datetime = prediction["prediction_date"]
            if isinstance(prediction_datetime, str):
                prediction_datetime = datetime.strptime(
                    prediction["prediction_date"], DT_FAP_RECRUIT
                )
            pred_field = [
                f"{prediction_user}",
                f"{prediction['team']} ({prediction['confidence']}) - {prediction_datetime.month}/{prediction_datetime.day}/{prediction_datetime.year}",
            ]

            if prediction["correct"] == 1:
                pred_field[0] = "✅ " + pred_field[0]
            elif prediction["correct"] == 0:
                pred_field[0] = "❌ " + pred_field[0]
            elif prediction["correct"] is None:
                pred_field[0] = "⌛ " + pred_field[0]

            predictions.append(dict(name=pred_field[0], value=pred_field[1]))

        embed = buildEmbed(
            title=f"Predictions for {self.recruit.name}", fields=predictions
        )
        embed.set_footer(text="✅ = Correct, ❌ = Wrong, ⌛ = TBD")

        await interaction.followup.send(embed=embed)


def is_walk_on(soup: BeautifulSoup) -> bool:
    icon = soup.find_all(attrs={"class": "icon-walkon"})
    return True if icon else False


def is_early_enrolee(soup: BeautifulSoup) -> bool:
    icon = soup.find_all(attrs={"class": "icon-time"})
    return True if icon else False


def is_early_signee(soup: BeautifulSoup) -> bool:
    icon = soup.find_all(attrs={"class": "signee-icon"})
    return True if icon else False


def reformat_weight(weight: str) -> str:
    try:
        int(weight)
    except TypeError:
        return "N/A"

    return f"{int(weight)} lbs."


def reformat_commitment_string(search_player: dict) -> Union[str, None]:
    if search_player["HighestRecruitInterestEventType"] == "HardCommit":
        return "Hard Commit"
    elif (
        search_player["HighestRecruitInterestEventType"] == "OfficialVisit"
        or search_player["HighestRecruitInterestEventType"] == "0"
    ):
        return None
    else:
        return search_player["HighestRecruitInterestEventType"].strip()


def reformat_composite_rating(cur_player: dict) -> str:
    if cur_player.get("CompositeRating", None) is None:
        return "0"
    else:
        return f"{cur_player['CompositeRating']:0.4f}"


def reformat_height(height: str) -> str:
    if height is None:
        return "N/A"

    double_apo = '" '
    height = f"{height.replace('-', double_apo)}{double_apo}"
    return height


def get_team_id(search_player: dict) -> int:
    if search_player["CommitedInstitutionTeamImage"] is None:
        return 0

    return int(
        search_player["CommitedInstitutionTeamImage"]
        .split("/")[-1]
        .split("_")[-1]
        .split(".")[0]
    )


def get_committed_school(all_team_ids: list[dict], team_id: int) -> Union[str, None]:
    try:
        if team_id > 0:
            for entry in all_team_ids:
                if team_id == entry[team_id]:
                    return all_team_ids[team_id]["school"]
        else:
            return None
    except KeyError:
        return None


def get_cb_experts(soup: BeautifulSoup, team_ids) -> list:
    experts = []

    try:
        cbs_long_expert = soup.find_all(attrs={"class": "prediction-list long expert"})
    except:  # noqa
        return experts

    if len(cbs_long_expert) == 0:
        return experts

    for expert in cbs_long_expert[0].contents:
        try:
            expert_name = expert.contents[1].string
            predicted_team = None

            if expert.find_all("img", src=True):
                predicted_team_id = int(
                    expert.find_all("img", src=True)[0]["src"]
                    .split("/")[-1]
                    .split(".")[0]
                )
                try:
                    predicted_team = (
                        team_ids[str(predicted_team_id)]
                        if predicted_team_id > 0
                        else None
                    )
                except KeyError:
                    predicted_team = "Unknown Team"
            else:
                if len(expert.find_all("b", attrs={"class": "question-icon"})) == 1:
                    predicted_team = "Undecided"

            # If the pick is undecided, it doesn't have a confidence
            if predicted_team != "Undecided":
                expert_confidence = f"{expert.contents[5].contents[1].text.strip()}, {expert.contents[5].contents[3].text.strip()}"
                expert_string = (
                    f"{expert_name} picks {predicted_team} ({expert_confidence})"
                )
            else:
                expert_string = f"{expert_name} is {predicted_team}"

            # I think 247 has some goofiness where there are some instances of "None" making a prediction, so I"m just not going to let those be added on
            if expert_name is not None:
                experts.append(expert_string)
        except:  # noqa
            continue

    return experts


def get_cb_predictions(soup: BeautifulSoup) -> list:
    crystal_balls = []

    predictions_header = soup.find_all(attrs={"class": "list-header-item"})

    if len(predictions_header) == 0:
        return crystal_balls

    cbs_long = cbs_one = None

    # When there are more than one predicted schools
    try:
        cbs_long = soup.find_all(attrs={"class": "prediction-list long"})
    except:  # noqa
        pass
    # When there is only one predicted school
    try:
        cbs_one = soup.find_all(attrs={"class": "prediction-list one"})
    except:  # noqa
        pass

    if len(cbs_long) > 0:
        for cb in cbs_long[0].contents:
            try:
                school_name = cb.contents[3].text.strip()
                school_weight = cb.contents[5].text.strip()
                school_string = f"{school_name}: {school_weight}"
                # If there is an "Undecided" in the list, it won't have a confidence with it
                if school_name != "Undecided":
                    school_confidence = f"{cb.contents[7].contents[1].text.strip()}, {cb.contents[7].contents[3].text.strip()}"
                    school_string += f"({school_confidence})"
                crystal_balls.append(school_string)
            except:  # noqa
                continue

        return crystal_balls
    elif len(cbs_one) > 0:
        single_school = cbs_one[0].contents[1]
        single_school_name = single_school.contents[3].text.strip()
        single_school_weight = single_school.contents[5].text.strip()
        try:
            single_school_confidence = f"{single_school.contents[7].contents[1].text.strip()}, {single_school.contents[7].contents[3].text.strip()}"
        except:  # noqa
            single_school_confidence = ""
        single_school_string = (
            f"{single_school_name}: {single_school_weight} ({single_school_confidence})"
        )

        crystal_balls.append(single_school_string)
    else:
        return ["N/A"]

    return crystal_balls


def get_all_time_ranking(soup: BeautifulSoup) -> int:
    recruit_rank = soup.find_all(
        attrs={"href": "https://247sports.com/Sport/Football/AllTimeRecruitRankings/"}
    )

    try:
        ranking = recruit_rank[1].contents[3].text

        if len(recruit_rank) > 1:
            return ranking
        else:
            return 0
    except IndexError:
        return 0


def get_national_ranking(cur_player: dict) -> int:
    if cur_player["NationalRank"] is None:
        return 0

    return cur_player["NationalRank"]


def get_position_ranking(cur_player: dict) -> int:
    if cur_player["PositionRank"] is None:
        return 0

    return cur_player["PositionRank"]


def get_state_ranking(cur_player: dict) -> str:
    if cur_player["StateRank"] is None:
        return "0"

    return cur_player["StateRank"]


def get_recruit_interests(search_player: dict) -> list[RecruitInterest]:
    reqs = requests.get(url=search_player["RecruitInterestsUrl"], headers=HEADERS)
    interests_soup = BeautifulSoup(reqs.content, "html.parser")
    interests = interests_soup.find(
        "ul", attrs={"class": "recruit-interest-index_lst"}
    ).find_all("li", recursive=False)
    all_interests = []

    # Goes through the list of interests and only adds in the ones that are offers
    for index, interest in enumerate(interests):
        offered = (
            interest.find("div", attrs={"class": "secondary_blk"})
            .find("span", attrs={"class": "offer"})
            .text.split(":")[1]
            .strip()
        )
        if offered == "Yes":
            all_interests.append(
                RecruitInterest(
                    school=interest.find("div", attrs={"class": "first_blk"})
                    .find("a")
                    .text.strip(),
                    offered=offered,
                    status=interest.find("div", attrs={"class": "first_blk"})
                    .find("span", attrs={"class": "status"})
                    .find("span")
                    .text,
                )
            )

    del reqs, interests, interests_soup

    return all_interests


def get_school_type(soup: BeautifulSoup) -> str:
    institution_type = soup.find_all(attrs={"data-js": "institution-selector"})

    if len(institution_type) == 0:
        return "High School"

    institution_type = str(institution_type[0].text).strip()
    return institution_type


def get_state_abbr(cur_player: dict) -> str:
    try:
        return RECRUIT_STATES[cur_player["Hometown"]["State"]]
    except KeyError:
        return cur_player["Hometown"]["State"]


def get_thumbnail(cur_player: dict) -> Union[None, str]:
    if cur_player["DefaultAssetUrl"] == "/.":
        return None
    else:
        return cur_player["DefaultAssetUrl"]


def get_twitter_handle(soup: BeautifulSoup) -> str:
    twitter = soup.find_all(attrs={"class": "tweets-comp"})
    try:
        twitter = twitter[0].attrs["data-username"]
        twitter = re.sub(r"[^\w*]+", "", twitter)
        return twitter
    except:  # noqa
        return "N/A"


def get_teams() -> list[str]:
    sql_teams = processMySQL(query=sqlTeamIDs, fetch="all")
    teams_list = [t["school"] for t in sql_teams]
    return teams_list


def get_individual_predictions(user_id: int, recruit):  # TODO Figure out the type hint
    sql_response = processMySQL(
        query=sqlGetPrediction,
        values=(user_id, recruit.twofourseven_profile),
        fetch="one",  # TODO Check on renaming variables
    )
    return sql_response


def search_result_info(new_search: list[Recruit]) -> str:
    result_info = ""
    for index, recruit in enumerate(new_search):
        if index < CROOT_SEARCH_LIMIT:
            result_info += (
                f"{list(search_reactions.keys())[index]}: "
                f"{recruit.year} - "
                f"{'⭐' * recruit.rating_stars if recruit.rating_stars else 'N/R'} - "
                f"{recruit.position} - "
                f"{recruit.name}\n"
            )
    return result_info


def createPredictionView(target_recruit: Recruit) -> PredictionView:
    view = PredictionView(target_recruit)
    if not target_recruit.committed == "Enrolled":
        view.crystal_ball.disabled = False
    view.scroll.disabled = False

    return view


def buildFootballRecruit(year: int, name: str) -> list[Recruit]:
    all_team_ids = processMySQL(fetch="all", query=sqlTeamIDs)
    name = name.split(" ")

    if len(name) == 1:
        _247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}"
        first_name = requests.get(url=_247_search, headers=HEADERS)
        first_name = json.loads(first_name.text)

        _247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.LastName={name[0]}"
        last_name = requests.get(url=_247_search, headers=HEADERS)
        last_name = json.loads(last_name.text)

        search_results = first_name + last_name
    elif len(name) == 2:
        _247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}&Player.LastName={name[1]}"

        search_results = requests.get(url=_247_search, headers=HEADERS)
        search_results = json.loads(search_results.text)
    else:
        raise RecruitException(
            f"Error occurred attempting to create 247sports search URL."
        )

    if not search_results:
        raise RecruitException(
            f"Unable to find [{name[0] if len(name) <= 1 else name[0] + ' ' + name[1]}] in the [{year}] class. Please try again!"
        )

    search_result_players = []

    for index, search_player in enumerate(search_results):
        cur_player = search_player["Player"]

        reqs = requests.get(url=search_player["Player"]["Url"], headers=HEADERS)
        soup = BeautifulSoup(reqs.content, "html.parser")

        # Put into separate variables for debugging purposes
        # red_shirt
        _247_highlights = cur_player.get("Url") + "Videos/"
        _247_profile = cur_player.get("Url", None)
        bio = cur_player.get("Bio", None)
        cb_experts = get_cb_experts(soup, all_team_ids)
        cb_predictions = get_cb_predictions(soup)
        city = cur_player["Hometown"].get("City", None)
        commitment_date = search_player.get("AnnouncementDate", None)
        committed = reformat_commitment_string(search_player)
        committed_school = get_committed_school(
            all_team_ids, get_team_id(search_player)
        )
        early_enrollee = is_early_enrolee(soup)
        early_signee = is_early_signee(soup)
        height = reformat_height(cur_player.get("Height", None))
        key = cur_player.get("Key", None)
        name = cur_player.get("FullName", None)
        position = cur_player["PrimaryPlayerPosition"].get("Abbreviation", None)
        ranking_all_time = get_all_time_ranking(soup)
        ranking_national = get_national_ranking(cur_player)
        ranking_position = get_position_ranking(cur_player)
        ranking_state = get_state_ranking(cur_player)
        rating_numerical = reformat_composite_rating(cur_player)
        rating_stars = cur_player.get("CompositeStarRating", None)
        recruit_interests = get_recruit_interests(search_player)
        recruit_interests_url = cur_player.get("RecruitInterestsUrl", None)
        school = cur_player["PlayerHighSchool"].get("Name", None)
        school_type = get_school_type(soup)
        scout_evaluation = cur_player.get("ScoutEvaluation", None)
        state = cur_player["Hometown"].get("State", None)
        state_abbr = get_state_abbr(cur_player)
        team_id = get_team_id(search_player)
        thumbnail = get_thumbnail(cur_player)
        twitter = get_twitter_handle(soup)
        walk_on = is_walk_on(soup)
        weight = reformat_weight(cur_player.get("Weight", None))
        year = search_player.get("Year", None)

        search_result_players.append(
            Recruit(
                twofourseven_highlights=_247_highlights,
                twofourseven_profile=_247_profile,
                bio=bio,
                cb_experts=cb_experts,
                cb_predictions=cb_predictions,
                city=city,
                commitment_date=commitment_date,
                committed=committed,
                committed_school=committed_school,
                early_enrollee=early_enrollee,
                early_signee=early_signee,
                height=height,
                key=key,
                name=name,
                position=position,
                ranking_all_time=ranking_all_time,
                ranking_national=ranking_national,
                ranking_position=ranking_position,
                ranking_state=ranking_state,
                rating_numerical=rating_numerical,
                rating_stars=rating_stars,
                recruit_interests=recruit_interests,
                recruit_interests_url=recruit_interests_url,
                # red_shirt=None,
                school=school,
                school_type=school_type,
                scout_evaluation=scout_evaluation,
                state=state,
                state_abbr=state_abbr,
                team_id=team_id,
                thumbnail=thumbnail,
                twitter=twitter,
                walk_on=walk_on,
                weight=weight,
                year=year,
            )
        )

        if index == CROOT_SEARCH_LIMIT - 1:
            break

    return search_result_players


class RecruitingCog(commands.Cog, name="Recruiting Commands"):
    group_recruit = app_commands.Group(
        name="predict",
        description="Recruiting prediction commands",
        guild_ids=[GUILD_PROD],
    )

    @app_commands.command(name="croot-bot", description="Look up a recruit")
    @app_commands.describe(
        year="The recruit's class year",
        search_name="Name of the recruit",
    )
    async def croot_bot(
        self, interaction: discord.Interaction, year: int, search_name: str
    ) -> None:
        logger.info(f"Searching for {year} {search_name.capitalize()}")
        await interaction.response.defer()

        if len(search_name) == 0:
            raise RecruitException(
                "A player's first and/or last search_name is required."
            )

        if len(str(year)) == 2:
            year += 2000
        # elif len(str(year)) == 1 or len(str(year)) == 3:
        elif 1 < len(str(year)) < 4:
            raise RecruitException("The search year must be two or four digits long.")

        if year > datetime.now().year + 5:
            raise RecruitException(
                "The search year must be within five years of the current class."
            )

        if year < 1869:
            raise RecruitException(
                "The search year must be after the first season of college football--1869."
            )

        logger.info(f"Searching for [{year} {search_name.capitalize()}]")

        global croot_search
        croot_search = buildFootballRecruit(year, search_name)

        logger.info(f"Found [{len(croot_search)}] results")

        if len(croot_search) == 1:
            embed = buildRecruitEmbed(croot_search[0])
            view = createPredictionView(croot_search[0])

            await interaction.followup.send(embed=embed, view=view)
        else:
            result_info = search_result_info(croot_search)

            view = RecruitListView(croot_search)
            embed = buildEmbed(
                title=f"Search Results for [{year} {search_name.capitalize()}]",
                fields=[dict(name="Search Results", value=result_info)],
            )

            await interaction.followup.send(embed=embed, view=view)

        logger.info(f"Sent search results for [{year} {search_name.capitalize()}]")

    @group_recruit.command(
        name="submit", description="Submit a prediction for a recruit"
    )
    @app_commands.describe(
        year="The year of the recruit's recruitting class",
        search_name="Name of the recruit",
    )
    async def predict_submit(
        self, interaction: discord.Interaction, year: int, search_recruit: str
    ) -> None:  # predict, stats, leaderboard, user
        logger.info(f"Starting a prediction for [{year}] [{search_recruit}]")
        if len(str(year)) == 2:
            year += 2000

        if year > datetime.now().year + 5:
            raise RecruitException(
                "The search year must be within five years of the current class."
            )

        if year < 1869:
            raise RecruitException(
                "The search year must be after the first season of college football--1869."
            )

        await interaction.response.defer(hidden=True)

        global prediction_search
        prediction_search = buildFootballRecruit(year, search_recruit)
        # TODO Left off here...
        if type(prediction_search) == commands.UserInputError:
            return await ctx.send(content=prediction_search, hidden=True)

        async def send_fap_convo(target_recruit):
            await initiate_fap(
                ctx=ctx, user=ctx.author, recruit=target_recruit, client=ctx.bot
            )

        if len(prediction_search) == 1:
            return await send_fap_convo(prediction_search[0])

        result_info = search_result_info(prediction_search)
        action_row = create_actionrow(*search_buttons)

        embed = build_embed(
            title=f"Search Results for [{year} {search_name.capitalize()}]",
            fields=[["Search Results", result_info]],
        )

        await ctx.send(embed=embed, components=[action_row], hidden=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecruitingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])
