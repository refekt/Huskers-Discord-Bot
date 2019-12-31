import datetime
import json
import re

import requests
from bs4 import BeautifulSoup
from bs4 import element
from discord.ext import commands

# from google import search
from utils.consts import headers
from utils.mysql import process_MySQL, sqlTeamIDs as TeamIDs

states = {'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
          'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA',
          'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM',
          'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
          'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
          'District Of Columbia': "DC"}


def position_abbr(position):
    long_positions = {'PRO': 'Pro-Style Quarterback', 'DUAL': 'Dual-Threat Quarterback', 'APB': 'All-Purpose Back', 'RB': 'Running Back', 'FB': 'Fullback', 'WR': 'Wide Receiver', 'TE': 'Tight End',
                      'OT': 'Offensive Tackle', 'OG': 'Offensive Guard', 'OC': 'Center', 'SDE': 'Strong-Side Defensive End', 'WDE': 'Weak-Side Defensive End', 'DT': 'Defensive Tackle',
                      'ILB': 'Inside Linebacker', 'OLB': 'Outside Linebacker', 'CB': 'Cornerback', 'S': 'Safety', 'ATH': 'Athlete', 'K': 'Kicker', 'P': 'Punter', 'LS': 'Long Snapper',
                      'RET': 'Returner'}
    return long_positions[position]


class RecruitInterest():
    school = None
    offered = None
    status = None

    def __init__(self, school, offered, status=None):
        self.school = school
        self.offered = offered
        self.status = status


class Recruit():
    x247_highlights = None
    x247_profile = None
    all_time_ranking = None
    bio = None
    city = None
    commitment_date = None
    committed = None
    committed_school = None
    early_enrollee = None
    early_signee = None
    height = None
    key = None
    name = None
    national_ranking = None
    position = None
    position_ranking = None
    predictions = None
    rating_numerical = None
    rating_stars = None
    recruit_interests = None
    recruit_interests_url = None
    red_shirt = None
    rivals_ID = None
    rivals_profile = None
    rivals_highlights = None
    school = None
    school_type = None
    scout_evaluation = None
    state = None
    state_abbr = None
    state_ranking = None
    thumbnail = None
    twitter = None
    walk_on = None
    weight = None
    year = None

    def __init__(self=None, x247_highlights=None, x247_profile=None, all_time_ranking=None, bio=None, city=None, commitment_date=None, committed=None, committed_school=None, early_enrollee=None,
                 early_signee=None, height=None, key=None, name=None, national_ranking=None, position=None, position_ranking=None, predictions=None, rating_numerical=None,
                 rating_stars=None, recruit_interests=None, recruit_interests_url=None, red_shirt=None, rivals_ID=None, rivals_profile=None, rivals_highlights=None, school=None, school_type=None,
                 scout_evaluation=None, state=None, state_abbr=None, state_ranking=None, thumbnail=None, twitter=None, walk_on=None, weight=None, year=None):
        self.x247_highlights = x247_highlights
        self.x247_profile = x247_profile
        self.all_time_ranking = all_time_ranking
        self.bio = bio
        self.city = city
        try:
            self.commitment_date = datetime.datetime.strptime(commitment_date, "%m/%d/%Y %I:%M:%S %p")
        except:
            self.commitment_date = commitment_date
        self.committed = committed
        self.committed_school = committed_school
        self.early_enrollee = early_enrollee
        self.early_signee = early_signee
        self.height = str(height).replace("-", "' ") + "\""
        self.key = key
        self.name = name
        self.national_ranking = national_ranking
        self.position = position_abbr(position)
        self.pos_abbr = position
        self.position_ranking = position_ranking
        self.predictions = predictions
        if rating_numerical is not None:
            self.rating_numerical = f"{float(rating_numerical / 100):.4f}"
        else:
            self.rating_numerical = None
        self.rating_stars = rating_stars
        self.recruit_interests = recruit_interests
        self.recruit_interests_url = recruit_interests_url
        self.red_shirt = red_shirt
        self.rivals_ID = rivals_ID
        self.rivals_profile = rivals_profile
        self.rivals_highlights = rivals_highlights
        self.school = school
        self.school_type = school_type
        self.scout_evaluation = scout_evaluation
        self.state = state
        self.state_abbr = state_abbr
        self.state_ranking = state_ranking
        self.thumbnail = thumbnail
        self.twitter = twitter
        self.walk_on = walk_on
        self.weight = str(weight) + " lbs"
        self.year = year


def FootballRecruit(year, name):
    search_results = x247_search = None
    team_ids_raw = process_MySQL(fetch="all", query=TeamIDs)
    team_ids = dict()

    for id in team_ids_raw:
        team_ids.update({id['id']: id['name']})

    if len(name) == 1:
        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}"
        first_name = requests.get(url=x247_search, headers=headers)
        first_name = json.loads(first_name.text)

        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.LastName={name[0]}"
        last_name = requests.get(url=x247_search, headers=headers)
        last_name = json.loads(last_name.text)

        search_results = first_name + last_name
    elif len(name) == 2:
        x247_search = f"https://247sports.com/Season/{year}-Football/Recruits.json?&Items=15&Page=1&Player.FirstName={name[0]}&Player.LastName={name[1]}"

        search_results = requests.get(url=x247_search, headers=headers)
        search_results = json.loads(search_results.text)
    else:
        print(f"Error occurred attempting to create 247sports search URL. Exiting..\n"
              f"{year}\n"
              f"{name}")
        return

    if not search_results:

        raise commands.UserInputError(f"Unable to find [{name[0] if len(name) <= 1 else name[0] + ' ' + name[1]}] in the [{year}] class. Please try again!")

    search_result_players = []

    def correct_commit_string():
        if player['HighestRecruitInterestEventType'] == "HardCommit":
            return "Hard Commit"
        elif player['HighestRecruitInterestEventType'] == "OfficialVisit":
            return None
        elif player['HighestRecruitInterestEventType'] == "0":
            return None
        else:
            return player['HighestRecruitInterestEventType']

    def school_type():
        school_type = soup.find_all(attrs={"data-js": "institution-selector"})

        if not len(school_type) == 0:
            school_type = str(school_type[0].text).strip()
            return school_type
        else:
            return "High School"

    def _247_highlights():
        return player['Player']['Url'] + 'Videos/'

    def early_enrolee():
        icon = soup.find_all(attrs={"class": "icon-time"})

        if icon:
            return True
        else:
            return False

    def early_signee():
        icon = soup.find_all(attrs={"class": "signee-icon"})

        if icon:
            return True
        else:
            return False

    def walk_on():
        icon = soup.find_all(attrs={"class": "icon-walkon"})

        if icon:
            return True
        else:
            return False

    def cb_predictions():
        cbs_raw = soup.find_all("h4")
        cbs = []

        try:
            for item in cbs_raw:
                if item.contents[0] == "Crystal Ball® Predictions":
                    cbs_raw = cbs_raw[1].parent.contents[5]
                    break
        except:
            return False

        for item in cbs_raw:
            if not type(item) == element.NavigableString and "%" in item.text:
                cbs.append(str(item.text).strip())

        return cbs

    def twitter_handle():
        twitter = soup.find_all(attrs={"class": "tweets-comp"})
        try:
            twitter = twitter[0].attrs["data-username"]
            twitter = re.sub(r"[^\w*]+", "", twitter)
            return twitter
        except:
            return "N/A"

    def national_ranking():
        rank = soup.find_all(href="https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool")

        if len(rank) > 1:
            return int(rank[1].contents[3].text)
        else:
            return False

    def state_ranking(player):
        rank = soup.find_all(attrs={"href": f"https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&State={states[player['Hometown']['State']]}"})

        ranking = 0
        try:
            ranking = int(rank[0].contents[3].text)
        except IndexError:
            pass

        if len(rank) == 1:
            return ranking
        else:
            return False

    def position_ranking(player):
        rank = soup.find_all(attrs={"href": f"https://247sports.com/Season/2020-Football/CompositeRecruitRankings/?InstitutionGroup=HighSchool&Position={player['PrimaryPlayerPosition']['Abbreviation']}"})

        ranking = 0
        try:
            ranking = int(rank[0].contents[3].text)
        except IndexError:
            pass

        if len(rank) == 1:
            return ranking
        else:
            return False

    def all_time_ranking():
        rank = soup.find_all(attrs={"href": "https://247sports.com/Sport/Football/AllTimeRecruitRankings/"})

        ranking = 0
        try:
            ranking = rank[1].contents[3].text
        except IndexError:
            pass

        if len(rank) > 1:
            return ranking
        else:
            return False

    # def rivals_profile(player):
    #     # query = f"site:rivals.com/content/prospects/{player['Year']}+{player['Player']['FullName'].replace(' ', '+')}"
    #     query = f"rivals.com {player['Year']} {player['Player']['FullName']}"
    #     results = search(
    #         query=query,
    #         tld="com",
    #         num=10
    #   )
    #     for q in results:
    #         if re.match(r"https://n.rivals.com/content/prospects/[0-9]{4}/\w{1,}-\w{1,}-\d{1,}", q):
    #             return q
    #         else:
    #             return None

    def rivals_ID(profile):
        if profile:
            ID = profile[profile.rfind("-") + 1:]
            return ID
        else:
            return None

    def rivals_highlights(ID):
        return f"https://n.rivals.com/content/prospects/{ID}/featured/videos"

    def recruit_interests():
        req = requests.get(url=player["RecruitInterestsUrl"], headers=headers)
        interests_soup = BeautifulSoup(req.content, "html.parser")

        interests = interests_soup.find_all(attrs={"class": "first_blk"})

        all_interests = []

        for index, interest in enumerate(interests):
            all_interests.append(
                RecruitInterest(
                    school=interest.contents[1].text.strip(),
                    offered="",
                    status=interest.contents[3].text.strip()
                )
            )

        del req
        del interests
        del interests_soup

        return all_interests

    for index, player in enumerate(search_results):
        p = player['Player']

        r = requests.get(url=player['Player']['Url'], headers=headers)
        soup = BeautifulSoup(r.content, "html.parser")

        # TODO Grab all the other variables; red_shirt, rivals_profile, fix the JUCO issue with "NCAA" not showing up and crystal balls if only one team

        team_id = 0
        if player['CommitedInstitutionTeamImage'] is not None:
            team_id = int(player['CommitedInstitutionTeamImage'].split('/')[-1].split('_')[-1].split('.')[0])  # Thank you Psy

        if p['NationalRank'] is None:
            p['NationalRank'] = national_ranking()

        if p['StateRank'] is None:
            p['StateRank'] = state_ranking(p)

        if p['PositionRank'] is None:
            p['PositionRank'] = position_ranking(p)

        # rivals_prof = rivals_profile(player)
        # rivals_id = rivals_ID(rivals_prof)

        search_result_players.append(
            Recruit(
                key=p['Key'],
                name=p['FullName'],
                city=p['Hometown']['City']if p['Hometown']['City'] else 'N/A' ,
                state=p['Hometown']['State'] if p['Hometown']['State'] else 'N/A',
                state_abbr=states[p['Hometown']['State']] if p['Hometown']['State'] else 'N/A',
                height=p['Height'],
                weight=p['Weight'],
                bio=p['Bio'],
                scout_evaluation=p['ScoutEvaluation'],
                x247_profile=p['Url'],
                x247_highlights=_247_highlights(),
                school=p['PlayerHighSchool']['Name'],
                school_type=school_type(),
                position=p['PrimaryPlayerPosition']['Abbreviation'],
                thumbnail=p['DefaultAssetUrl'],
                rating_numerical=p['CompositeRating'],
                rating_stars=p['CompositeStarRating'],
                national_ranking=p['NationalRank'],
                state_ranking=p['StateRank'],
                position_ranking=p['PositionRank'],
                committed=correct_commit_string(),
                committed_school=team_ids[team_id] if team_id > 0 else None,
                commitment_date=player['AnnouncementDate'],
                recruit_interests=recruit_interests(),
                recruit_interests_url=player["RecruitInterestsUrl"],
                year=player['Year'],
                early_enrollee=early_enrolee(),
                early_signee=early_signee(),
                all_time_ranking=all_time_ranking(),
                predictions=cb_predictions(),
                twitter=twitter_handle(),
                walk_on=walk_on(),
                # rivals_profile=rivals_prof,
                # rivals_ID=rivals_id,
                # rivals_highlights=rivals_highlights(rivals_id)
           )
        )

    return search_result_players
