import json
import logging
import re
from datetime import datetime
from typing import Union, Any, Optional

import discord.ext.commands
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from discord import app_commands
from discord.ext import commands
from requests import Response, JSONDecodeError

from helpers.constants import (
    CROOT_SEARCH_LIMIT,
    DT_FAP_RECRUIT,
    GUILD_PROD,
    HEADERS,
    RECRUIT_STATES,
    TZ,
)
from helpers.embed import buildEmbed, buildRecruitEmbed
from helpers.misc import checkYearValid
from helpers.mysql import (
    processMySQL,
    sqlGetIndividualPrediction,
    sqlGetPrediction,
    sqlInsertPrediction,
    sqlTeamIDs,
)
from objects.Exceptions import RecruitException
from objects.Logger import discordLogger, is_debugging
from objects.Recruits import RecruitInterest, Recruit

logger = discordLogger(
    name=__name__,
    level=logging.DEBUG if is_debugging() else logging.INFO,
)

croot_search: list[Recruit] = []
prediction_search: list[Recruit] = []
search_reactions: dict[str, int] = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4}

CURRENT_CLASS: int = datetime.now().year
NO_MORE_PREDS: int = datetime.now().year

__all__: list[str] = ["RecruitingCog"]


class RecruitListView(discord.ui.View):
    """
    The View for each search button 1-5
    """

    def __init__(self, recruit_search: list[Recruit]) -> None:
        super().__init__()
        self.croot_search: list[Recruit] = recruit_search

        logger.info("Creating recruit search buttons")
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

        reaction_pressed: int = int(interaction.data["custom_id"][-1])

        logger.info(f"Croot-bot search button #{reaction_pressed + 1} pressed")

        embed: discord.Embed = buildRecruitEmbed(croot_search[reaction_pressed])
        view: discord.ui.View = createPredictionView(croot_search[reaction_pressed])

        logger.info("Sending a new recruit embed")
        await interaction.edit_original_response(embed=embed, view=view)

        return True


class PredictionTeamModal(discord.ui.Modal, title="What school and confidence?"[:45]):
    """
    The Modal for receiving text input to search a school
    """

    def __init__(self, recruit: Recruit) -> None:
        super().__init__()
        self.recruit: Recruit = recruit

    max_len: int = 44
    prediction_school: discord.ui.TextInput = discord.ui.TextInput(
        label="What is your school prediction?"[:max_len]
    )
    prediction_confidence: discord.ui.TextInput = discord.ui.TextInput(
        label="Prediction confidence 1 (low) to 10 (high)"[:max_len]
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        logger.info("Prediction modal initiated")
        await interaction.response.defer(ephemeral=True)

        global user_prediction
        user_prediction.school = self.prediction_school
        user_prediction.confidence = self.prediction_confidence
        self.stop()

        logger.info("Confirming if recruit is already committed to a school")
        formatted_team_list: list[str] = [team.lower() for team in get_teams()]
        if user_prediction.school.value.lower() in formatted_team_list:
            team_index: int = formatted_team_list.index(
                user_prediction.school.value.lower()
            )
            team_prediction: str = get_teams()[team_index]

            if self.recruit.committed_school == team_prediction:
                raise RecruitException(
                    f"{self.recruit.name} is already committed to {self.recruit.committed_school}!"
                )

        else:
            raise RecruitException(
                "Your team choice was not a valid team. Please try again!"
            )

        logger.info("Checking if a prediction exists already")
        previous_prediction: dict = get_individual_predictions(
            user_id=interaction.user.id, recruit=self.recruit
        )
        if previous_prediction:
            table_id = previous_prediction["id"]
        else:
            table_id = 0

        logger.info("Inserting or updating prediction")
        dt_now: datetime = datetime.now(tz=TZ)

        processMySQL(
            query=sqlInsertPrediction,
            values=(
                table_id,  # id
                interaction.user.name,  # user
                interaction.user.id,  # user_id
                self.recruit.name,  # recruit_name
                self.recruit.twofourseven_profile,  # recruit_profile
                self.recruit.year,  # recruit_class
                user_prediction.school.value,  # team
                int(user_prediction.confidence.value),  # confidence
                dt_now,  # prediction_date
                user_prediction.school.value,  # team
                int(user_prediction.confidence.value),  # confidence
                dt_now,  # prediction_date
            ),
        )

        await interaction.followup.send(
            f"Your prediction of [{self.recruit.name}] to [{str(user_prediction.school.value).capitalize()}] with a [{user_prediction.confidence}] level has been logged!",
            ephemeral=True,
        )
        logger.info("Prediction was recorded!")

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        raise RecruitException(str(error))


class PredictionView(discord.ui.View):
    """
    The View to manage submitting and retrieving predictions
    """

    def __init__(self, recruit: Recruit) -> None:
        super().__init__()
        self.recruit: Recruit = recruit

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
        modal: discord.ui.Modal = PredictionTeamModal(self.recruit)
        await interaction.response.send_modal(modal)
        await modal.wait()

    @discord.ui.button(label="📜", disabled=True)
    async def scroll(
        self, interaction: discord.Interaction, button: discord.Button
    ) -> None:
        logger.info(f"Retrieving predictions for {self.recruit.name}...")
        await interaction.response.defer()

        individual_preds: Optional[list[dict, ...]] = processMySQL(
            query=sqlGetIndividualPrediction,
            fetch="all",
            values=(self.recruit.twofourseven_profile,),
        )
        if individual_preds is None:
            raise RecruitException("This recruit has no predictions.")

        logger.info(f"Compiling {len(individual_preds)} predictions")
        predictions: list[Optional[dict]] = []
        for index, prediction in enumerate(individual_preds):
            try:
                prediction_user: Union[
                    discord.Member, str
                ] = interaction.guild.get_member(prediction["user_id"])
                prediction_user = prediction_user.display_name
            except:  # noqa
                prediction_user = prediction["user"]

            if prediction_user is None:
                prediction_user = prediction["user"]

            prediction_datetime: datetime | str = prediction["prediction_date"]
            if isinstance(prediction_datetime, str):
                prediction_datetime = datetime.strptime(
                    prediction["prediction_date"], DT_FAP_RECRUIT
                )
            pred_field: list[str] = [
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

        embed: discord.Embed = buildEmbed(
            title=f"Predictions for {self.recruit.name}", fields=predictions
        )
        embed.set_footer(text="✅ = Correct, ❌ = Wrong, ⌛ = TBD")

        await interaction.followup.send(embed=embed)


class UserPrediction:
    def __init__(
        self,
        school: Any,
        confidence: Any,
    ) -> None:
        self.school: discord.ui.TextInput = school
        self.confidence: discord.ui.Select = confidence


user_prediction: UserPrediction = UserPrediction(None, None)


def is_walk_on(soup: BeautifulSoup) -> bool:
    icon: ResultSet = soup.find_all(attrs={"class": "icon-walkon"})
    return True if icon else False


def is_early_enrolee(soup: BeautifulSoup) -> bool:
    icon: ResultSet = soup.find_all(attrs={"class": "icon-time"})
    return True if icon else False


def is_early_signee(soup: BeautifulSoup) -> bool:
    icon: ResultSet = soup.find_all(attrs={"class": "signee-icon"})
    return True if icon else False


def reformat_weight(weight: str) -> str:
    try:
        int(weight)
    except TypeError:
        return "N/A"

    return f"{int(weight)} lbs."


def reformat_commitment_string(search_player: dict) -> str | None:
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

    double_apo: str = '" '
    height: str = f"{height.replace('-', double_apo)}{double_apo}"
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


def get_committed_school(all_team_ids: list[dict], team_id: int) -> str | None:
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
    logger.info("Collecting expert crystal ball predictions")
    experts: list[str] = []

    try:
        cbs_long_expert: ResultSet = soup.find_all(
            attrs={"class": "prediction-list long expert"}
        )
    except:  # noqa
        return experts

    if len(cbs_long_expert) == 0:
        logger.info("Returning single expert")
        return experts

    for index, expert in enumerate(cbs_long_expert[0].contents):
        logger.info(
            f"Searching expert #{index + 1} out of {len(cbs_long_expert[0].contents)}"
        )
        try:
            expert_name: str = expert.contents[1].string
            predicted_team: str = ""

            if expert.find_all("img", src=True):
                predicted_team_id: int = int(
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
                expert_confidence: str = f"{expert.contents[5].contents[1].text.strip()}, {expert.contents[5].contents[3].text.strip()}"
                expert_string: str = (
                    f"{expert_name} picks {predicted_team} ({expert_confidence})"
                )
            else:
                expert_string = f"{expert_name} is {predicted_team}"

            # I think 247 has some goofiness where there are some instances of "None" making a prediction, so I"m just not going to let those be added on
            if expert_name is not None:
                experts.append(expert_string)
        except:  # noqa
            continue

    logger.info("Returning list of crystal ball predictions")
    return experts


def get_cb_predictions(soup: BeautifulSoup) -> list:
    logger.info("Getting crystal ball predictions")
    crystal_balls: list[str] = []

    predictions_header: ResultSet = soup.find_all(attrs={"class": "list-header-item"})

    if len(predictions_header) == 0:
        logger.info("No crystal ball predictions found")
        return crystal_balls

    cbs_long: Optional[ResultSet] = None
    cbs_one: Optional[ResultSet] = None

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
        for index, cb in enumerate(cbs_long[0].contents):
            logger.info(
                f"Searching long list of predictions #{index} out of {len(cbs_long[0].contents)}"
            )
            try:
                school_name: str = cb.contents[3].text.strip()
                school_weight: str = cb.contents[5].text.strip()
                school_string: str = f"{school_name}: {school_weight}"
                # If there is an "Undecided" in the list, it won't have a confidence with it
                if school_name != "Undecided":
                    school_confidence: str = f"{cb.contents[7].contents[1].text.strip()}, {cb.contents[7].contents[3].text.strip()}"
                    school_string += f"({school_confidence})"
                crystal_balls.append(school_string)
            except:  # noqa
                continue

        return crystal_balls
    elif len(cbs_one) > 0:
        logger.info(f"Searching short list of crystal ball predictions")
        single_school: str = cbs_one[0].contents[1]
        single_school_name: str = single_school.contents[3].text.strip()  # noqa
        single_school_weight: str = single_school.contents[5].text.strip()  # noqa
        try:
            single_school_confidence: str = f"{single_school.contents[7].contents[1].text.strip()}, {single_school.contents[7].contents[3].text.strip()}"  # noqa
        except:  # noqa
            single_school_confidence = ""
        single_school_string: str = (
            f"{single_school_name}: {single_school_weight} ({single_school_confidence})"
        )

        crystal_balls.append(single_school_string)
    else:
        return ["N/A"]

    logger.info("Returning crystal ball results")
    return crystal_balls


def get_all_time_ranking(soup: BeautifulSoup) -> int:
    recruit_rank: ResultSet = soup.find_all(
        attrs={"href": "https://247sports.com/Sport/Football/AllTimeRecruitRankings/"}
    )

    try:
        ranking: int = recruit_rank[1].contents[3].text

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
    logger.info("Getting recruit interests")

    all_interests: list[Optional[RecruitInterest]] = []

    reqs: requests.Response = requests.get(
        url=search_player["RecruitInterestsUrl"], headers=HEADERS
    )
    interests_soup: BeautifulSoup = BeautifulSoup(reqs.content, "html.parser")
    interests: ResultSet = interests_soup.find(
        "ul", attrs={"class": "recruit-interest-index_lst"}
    ).find_all("li", recursive=False)

    # Goes through the list of interests and only adds in the ones that are offers
    for index, interest in enumerate(interests):
        offered: str = (
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

    logger.info("Returning recruit interests")
    return all_interests


def get_school_type(soup: BeautifulSoup) -> str:
    institution_type: ResultSet | str = soup.find_all(
        attrs={"data-js": "institution-selector"}
    )

    if len(institution_type) == 0:
        return "High School"

    institution_type = str(institution_type[0].text).strip()
    return institution_type


def get_state_abbr(cur_player: dict) -> str:
    try:
        return RECRUIT_STATES[cur_player["Hometown"]["State"]]
    except KeyError:
        return cur_player["Hometown"]["State"]


def get_thumbnail(cur_player: dict) -> None | str:
    if cur_player["DefaultAssetUrl"] == "/.":
        return None
    else:
        return cur_player["DefaultAssetUrl"]


def get_twitter_handle(soup: BeautifulSoup) -> str:
    twitter: ResultSet | str = soup.find_all(attrs={"class": "tweets-comp"})
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


def get_individual_predictions(user_id: int, recruit) -> Union[dict, list[dict]]:
    sql_response: list[dict, ...] = processMySQL(
        query=sqlGetPrediction,
        values=(user_id, recruit.twofourseven_profile),
        fetch="one",
    )
    return sql_response


def search_result_info(new_search: list[Recruit]) -> str:
    logger.info("Building search result string")
    result_info: str = ""
    for index, recruit in enumerate(new_search):
        if index < CROOT_SEARCH_LIMIT:
            result_info += (
                f"{list(search_reactions.keys())[index]}: "
                f"{recruit.year} - "
                f"{'⭐' * int(recruit.rating_stars) if recruit.rating_stars else 'N/R'} - "
                f"{recruit.position} - "
                f"{recruit.name}\n"
            )
    return result_info


def createPredictionView(target_recruit: Recruit) -> PredictionView:
    view: PredictionView = PredictionView(target_recruit)
    if not target_recruit.committed == "Enrolled":
        view.crystal_ball.disabled = False
    view.scroll.disabled = False

    return view


def buildFootballRecruit(year: int, name: str) -> list[Recruit]:
    logger.info("Building Football Recruit object")

    if len(str(year)) == 2:
        year += 2000

    assert checkYearValid(year), RecruitException(
        f"The provided year is not valid: {year}"
    )

    logger.info("Collecting team IDs")
    all_team_ids: Optional[list[dict, ...]] = processMySQL(
        fetch="all", query=sqlTeamIDs
    )
    name: list[str] = name.split(" ")

    if len(name) == 1:
        logger.info("Searching the single name for first and last name")

        _247_search: str = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=5&Page=1&Player.FirstName={name[0]}"
        first_name: Union[Response, list[dict]] = requests.get(
            url=_247_search, headers=HEADERS
        )

        if first_name.status_code == 200:
            try:
                first_name = first_name.json()
            except JSONDecodeError:
                pass

        _247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=5&Page=1&Player.LastName={name[0]}"
        last_name: Union[Response, list[dict]] = requests.get(
            url=_247_search, headers=HEADERS
        )
        if last_name.status_code == 200:
            try:
                last_name = last_name.json()
            except JSONDecodeError:
                pass

        assert isinstance(first_name, list) and isinstance(
            last_name, list
        ), RecruitException(
            f"Unable to find {year} {' '.join(name)}. Please try again!"
        )

        search_results = first_name + last_name
    elif len(name) == 2:
        logger.info("Searching the combined name for first and last name")
        _247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}&Player.LastName={name[1]}"

        search_results = requests.get(url=_247_search, headers=HEADERS)
        if not search_results.status_code == 200:
            raise RecruitException(f"No results found from search.")
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
        if index + 1 > CROOT_SEARCH_LIMIT:
            logger.info("Stopping search because search limit reached")
            break

        logger.info(f"Compiling search result #{index + 1} of {len(search_results)}")
        cur_player = search_player["Player"]

        reqs = requests.get(url=search_player["Player"]["Url"], headers=HEADERS)
        soup: BeautifulSoup = BeautifulSoup(reqs.content, "html.parser")

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
        _name = cur_player.get("FullName", None)
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
        _year = search_player.get("Year", None)

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
                name=_name,
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
                year=_year,
            )
        )

        if index == CROOT_SEARCH_LIMIT - 1:
            logger.info("Stopping loop because too many results found")
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

        assert checkYearValid(year), RecruitException(
            f"The provided year is not valid: {year}"
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
        year="The year of the recruit's recruiting class",
        search_name="Name of the recruit",
    )
    async def predict_submit(  # predict, stats, leaderboard, user
        self, interaction: discord.Interaction, year: int, search_name: str
    ) -> None:
        logger.info(f"Starting a prediction for [{year}] [{search_name}]")

        if not len(search_name.split(" ")) == 2:
            raise RecruitException("You can only search by full name.")

        if len(str(year)) == 2:
            year += 2000

        assert checkYearValid(year), RecruitException(
            f"The provided year is not valid: {year}"
        )

        global prediction_search
        prediction_search = buildFootballRecruit(year, search_name)

        modal = PredictionTeamModal(prediction_search[0])
        await interaction.response.send_modal(modal)
        await modal.wait()

    # TODO predict_show

    # TODO predict_leaderboard


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecruitingCog(bot), guilds=[discord.Object(id=GUILD_PROD)])


logger.info(f"{str(__name__).title()} module loaded!")
