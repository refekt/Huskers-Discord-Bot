from objects.Logger import discordLogger

logger = discordLogger(__name__)

__all__ = ["Recruit", "RecruitInterest"]

logger.info(f"{str(__name__).title()} module loaded!")


class RecruitInterest:
    def __init__(self, school: str, offered: str, status: str = None) -> None:
        self.offered = offered
        self.school = school
        self.status = status


class Recruit:
    def __init__(
        self,
        bio: str,
        cb_experts,
        cb_predictions,
        city: str,
        commitment_date: str,
        committed,
        committed_school: str,
        early_enrollee,
        early_signee,
        height: str,
        key: int,
        name: str,
        position: str,
        ranking_all_time: int,
        ranking_national: int,
        ranking_position: int,
        ranking_state: str,
        rating_numerical: str,
        rating_stars: str,
        recruit_interests: list[RecruitInterest],
        recruit_interests_url: str,
        school: str,
        school_type: str,
        scout_evaluation: str,
        state: str,
        state_abbr: str,
        team_id: int,
        thumbnail: str,
        twitter: str,
        twofourseven_highlights: str,
        twofourseven_profile: str,
        walk_on: bool,
        weight: str,
        year: int,
    ):
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
        self.twofourseven_highlights = twofourseven_highlights
        self.twofourseven_profile = twofourseven_profile
        self.walk_on = walk_on
        self.weight = weight
        self.year = year
