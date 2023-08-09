import math
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, RootModel, constr

Date = constr(pattern=r"\d{2}/\d{2}/\d{4}")


class LevelsInfoEnum(Enum):
    LEVEL_1 = "Level1"
    LEVEL_2 = "Level2"


class PromotionType(Enum):
    URL_REWARD = "urlreward"  # Activity completed by visiting the URL
    QUIZ = "quiz"  # Answer from 5 to 10 questions

    SEARCH = "search"  # PC Search
    EMPTY = ""  # prevents enum casting to fail in case of empty string

    WELCOME_TOUR = "welcometour"  # Same as url reward, but granted only once

    # streak keepers
    STREAK = "streak"
    STREAK_BONUS = "streakbonus"
    COACH_MARKS = "coachmarks"


class Promotion(BaseModel):
    name: str
    offerId: str
    complete: bool
    counter: int
    activityProgress: int
    activityProgressMax: int
    pointProgressMax: int
    pointProgress: int
    promotionType: PromotionType
    promotionSubtype: str
    title: str
    extBannerTitle: str
    titleStyle: str
    theme: str
    description: str
    showcaseTitle: str
    showcaseDescription: str
    imageUrl: str
    dynamicImage: str
    destinationUrl: str
    linkText: str
    hash: str
    activityType: str
    isRecurring: bool
    isHidden: bool
    isTestOnly: bool
    isGiveEligible: bool

    def is_enabled(self) -> bool:
        return not self.isHidden and not self.isTestOnly

    def is_completable(self) -> bool:
        return (
            self.is_enabled()
            and not self.complete
            and self.promotionType in (PromotionType.URL_REWARD, PromotionType.QUIZ)
        )


class LevelInfo(BaseModel):
    activeLevel: LevelsInfoEnum


class SearchCounter(BaseModel):
    name: str
    offerId: str
    complete: bool
    pointProgress: int
    pointProgressMax: int

    def is_completable(self) -> bool:
        return not self.complete

    @staticmethod
    def get_points_per_search() -> int:
        """
        Returns the amount of points earned per single search.
        """

        return 3  # TODO: this could be also parsed from `description`

    def get_needed_searches_amount(self) -> int:
        """
        Returns the amount of searches needed to reach the maximum for the day.
        """

        delta_points = self.pointProgressMax - self.pointProgress
        count_searches: float = delta_points / self.get_points_per_search()
        count_searches_ceil = math.ceil(count_searches)
        return int(count_searches_ceil)


class Counters(BaseModel):
    # two items expected: actual pc searches counter, and bing searches counter
    pcSearch: List[SearchCounter] = Field(..., min_length=2, max_length=2)

    # one item expected: actual mobile searches counter
    mobileSearch: Optional[List[SearchCounter]] = Field(
        None, min_length=1, max_length=1
    )


class UserStatus(BaseModel):
    levelInfo: LevelInfo
    availablePoints: int
    counters: Counters


# RootModel instead of BaseModel because of:
# https://docs.pydantic.dev/latest/usage/models/#rootmodel-and-custom-root-types
class DailySetPromotions(RootModel):
    root: Dict[
        Date, List[Promotion]
    ]  # needed to parse automatically `Date` keys, since they are dynamic

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]


class Dashboard(BaseModel):
    userStatus: UserStatus
    promotionalItem: Optional[Promotion]
    dailySetPromotions: DailySetPromotions
    # punchCards: List[Any]
    morePromotions: List[Promotion]

    def level(self) -> LevelsInfoEnum:
        """
        Returns the current user level.
        """

        return self.userStatus.levelInfo.activeLevel

    def points(self) -> int:
        """
        Returns the amount of points available.
        """

        return self.userStatus.availablePoints

    def can_search_on_pc(self) -> bool:
        """
        Returns True if any PC search is missing, False otherwise.
        """

        return self.userStatus.counters.pcSearch[0].is_completable()

    def can_search_on_mobile(self) -> bool:
        """
        Returns True if any Mobile search is missing, False otherwise.
        """

        if self.level() is LevelsInfoEnum.LEVEL_1:
            return False

        assert self.userStatus.counters.mobileSearch is not None
        return self.userStatus.counters.mobileSearch[0].is_completable()

    def amount_of_pc_searches(self) -> int:
        """
        Returns the amount of PC searches that are needed to be executed.

        Returns 0 if no PC search is needed, or the corresponding counter is disabled.
        """

        if not self.can_search_on_pc():
            return 0

        return self.userStatus.counters.pcSearch[0].get_needed_searches_amount()

    def amount_of_mobile_searches(self) -> int:
        """
        Returns the amount of Mobile searches that are needed to be executed.

        Returns 0 if no Mobile search is needed, or the corresponding counter is disabled.
        """

        if not self.can_search_on_mobile():
            return 0

        return self.userStatus.counters.mobileSearch[0].get_needed_searches_amount()
