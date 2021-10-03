import json
import re

import requests
from bs4 import BeautifulSoup

from utilities.constants import CROOT_SEARCH_LIMIT, HEADERS, UserError
from utilities.mysql import Process_MySQL, sqlTeamIDs


class RecruitInterest:
    offered = None
    school = None
    status = None

    def __init__(self, school: str, offered: str, status: str = None):
        self.offered = offered
        self.school = school
        self.status = status


class Recruit:
    def __init__(
        self,
        _247_highlights,
        _247_profile,
        ranking_all_time,
        bio,
        city,
        commitment_date,
        committed,
        committed_school,
        early_enrollee,
        early_signee,
        cb_experts,
        height,
        key,
        name,
        ranking_national,
        position,
        ranking_position,
        cb_predictions,
        rating_numerical,
        rating_stars,
        recruit_interests,
        recruit_interests_url,
        school,
        school_type,
        scout_evaluation,
        state,
        state_abbr,
        ranking_state,
        thumbnail,
        twitter,
        walk_on,
        weight,
        year,
        team_id,
    ):
        self._247_highlights = _247_highlights
        self._247_profile = _247_profile
        self.bio = bio
        self.cb_experts = cb_experts
        self.cb_predictions = cb_predictions
        self.city = city
        self.commitment_date = commitment_date
        self.committed = committed
        self.committed_school = committed_school
        self.early_enrollee = early_enrollee
        self.early_signee = early_signee
        self.height = height
        self.key = key
        self.name = name
        self.position = position
        self.ranking_all_time = ranking_all_time
        self.ranking_national = ranking_national
        self.ranking_position = ranking_position
        self.ranking_state = ranking_state
        self.rating_numerical = rating_numerical
        self.rating_stars = rating_stars
        self.recruit_interests = recruit_interests
        self.recruit_interests_url = recruit_interests_url
        self.school = school
        self.school_type = school_type
        self.scout_evaluation = scout_evaluation
        self.state = state
        self.state_abbr = state_abbr
        self.team_id = team_id
        self.thumbnail = thumbnail
        self.twitter = twitter
        self.walk_on = walk_on
        self.weight = weight
        self.year = year


states = {
    "Alabama": "AL",
    "Alaska": "AK",
    "American Samoa": "AS",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "British Columbia": "BC",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District Of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
long_positions = {
    "APB": "All-Purpose Back",
    "ATH": "Athlete",
    "CB": "Cornerback",
    "DL": "Defensive Lineman",
    "DT": "Defensive Tackle",
    "DUAL": "Dual-Threat Quarterback",
    "Edge": "Edge",
    "FB": "Fullback",
    "ILB": "Inside Linebacker",
    "IOL": "Interior Offensive Lineman",
    "K": "Kicker",
    "LB": "Linebacker",
    "LS": "Long Snapper",
    "OC": "Center",
    "OG": "Offensive Guard",
    "OLB": "Outside Linebacker",
    "OT": "Offensive Tackle",
    "P": "Punter",
    "PRO": "Pro-Style Quarterback",
    "QB": "Quarterback",
    "RB": "Running Back",
    "RET": "Returner",
    "S": "Safety",
    "SDE": "Strong-Side Defensive End",
    "TE": "Tight End",
    "WDE": "Weak-Side Defensive End",
    "WR": "Wide Receiver",
}


def get_team_id(search_player):
    if search_player["CommitedInstitutionTeamImage"] is not None:
        return int(
            search_player["CommitedInstitutionTeamImage"]
            .split("/")[-1]
            .split("_")[-1]
            .split(".")[0]
        )
    else:
        return 0


def reformat_commitment_string(search_player):
    if search_player["HighestRecruitInterestEventType"] == "HardCommit":
        return "Hard Commit"
    elif search_player["HighestRecruitInterestEventType"] == "OfficialVisit":
        return None
    elif search_player["HighestRecruitInterestEventType"] == "0":
        return None
    else:
        return search_player["HighestRecruitInterestEventType"].strip()


def get_committed_school(all_team_ids, team_id):
    try:
        if team_id > 0:
            for entry in all_team_ids:
                if team_id == entry[team_id]:
                    return all_team_ids[team_id]
        else:
            return None
    except KeyError:
        return None


def is_early_enrolee(soup):
    icon = soup.find_all(attrs={"class": "icon-time"})
    return True if icon else False


def reformat_height(height: str):
    if height is None:
        return "N/A"
    else:
        double_apo = '" '
        height = f"{height.replace('-', double_apo)}{double_apo}"
    return height


def is_early_signee(soup):
    icon = soup.find_all(attrs={"class": "signee-icon"})
    return True if icon else False


def get_cb_experts(soup, team_ids) -> list:
    experts = []

    try:
        cbs_long_expert = soup.find_all(attrs={"class": "prediction-list long expert"})
    except:
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

            # If the pick is undecided, it doesn"t have a confidence
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
        except:
            continue

    return experts


def get_cb_predictions(soup):
    crystal_balls = []

    predictions_header = soup.find_all(attrs={"class": "list-header-item"})

    if len(predictions_header) == 0:
        return crystal_balls

    cbs_long = cbs_one = None

    # When there are more than one predicted schools
    try:
        cbs_long = soup.find_all(attrs={"class": "prediction-list long"})
    except:
        pass
    # When there is only one predicted school
    try:
        cbs_one = soup.find_all(attrs={"class": "prediction-list one"})
    except:
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
            except:
                continue

        return crystal_balls
    elif len(cbs_one) > 0:
        single_school = cbs_one[0].contents[1]
        single_school_name = single_school.contents[3].text.strip()
        single_school_weight = single_school.contents[5].text.strip()
        try:
            single_school_confidence = f"{single_school.contents[7].contents[1].text.strip()}, {single_school.contents[7].contents[3].text.strip()}"
        except:
            single_school_confidence = ""
        single_school_string = (
            f"{single_school_name}: {single_school_weight} ({single_school_confidence})"
        )

        crystal_balls.append(single_school_string)
    else:
        return ["N/A"]

    return crystal_balls


def get_all_time_ranking(soup):
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


def get_national_ranking(cur_player):
    if cur_player["NationalRank"] is not None:
        return cur_player["NationalRank"]
    else:
        return 0


def get_position_ranking(cur_player):
    if cur_player["PositionRank"] is not None:
        return cur_player["PositionRank"]
    else:
        return 0


def get_state_ranking(cur_player):
    if cur_player["StateRank"] is not None:
        return cur_player["StateRank"]
    else:
        return 0


def reformat_composite_rating(cur_player):
    if cur_player.get("CompositeRating", None) is None:
        return "0"
    else:
        return f"{cur_player['CompositeRating']:0.4f}"


def get_recruit_interests(search_player):
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


def get_school_type(soup):
    institution_type = soup.find_all(attrs={"data-js": "institution-selector"})

    if not len(institution_type) == 0:
        institution_type = str(institution_type[0].text).strip()
        return institution_type
    else:
        return "High School"


def get_state_abbr(cur_player):
    try:
        return states[cur_player["Hometown"]["State"]]
    except KeyError:
        return cur_player["Hometown"]["State"]


def get_thumbnail(cur_player):
    if cur_player["DefaultAssetUrl"] == "/.":
        return None
    else:
        return cur_player["DefaultAssetUrl"]


def get_twitter_handle(soup):
    twitter = soup.find_all(attrs={"class": "tweets-comp"})
    try:
        twitter = twitter[0].attrs["data-username"]
        twitter = re.sub(r"[^\w*]+", "", twitter)
        return twitter
    except:
        return "N/A"


def get_walk_on(soup):
    icon = soup.find_all(attrs={"class": "icon-walkon"})

    if icon:
        return True
    else:
        return False


def reformat_weight(weight: str):
    return f"{int(weight)} lbs."


def FootballRecruit(year, name):
    all_team_ids = Process_MySQL(fetch="all", query=sqlTeamIDs)
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
        raise UserError(f"Error occurred attempting to create 247sports search URL.")

    if not search_results:
        raise UserError(
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
        walk_on = get_walk_on(soup)
        weight = reformat_weight(cur_player.get("Weight", None))
        year = search_player.get("Year", None)

        search_result_players.append(
            Recruit(
                _247_highlights=_247_highlights,
                _247_profile=_247_profile,
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
