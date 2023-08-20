import copy
import math
from enum import Enum, auto
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


class QuizType(Enum):
    """
    Differentiation of possible Quiz types.
    """

    # This quiz is a simple choice between two elements.
    # It does not have a Start button to click.
    CHOICE_BETWEEN_TWO = auto()

    # These quizzes have a Start button to click.
    # They can be either questions with four or eight answers.
    THREE_QUESTIONS_FOUR_ANSWERS = auto()
    THREE_QUESTIONS_EIGHT_ANSWERS = auto()


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
            and self.promotionType
            in (
                PromotionType.URL_REWARD,
                PromotionType.QUIZ,
                PromotionType.WELCOME_TOUR,
            )
        )


class LevelInfo(BaseModel):
    activeLevel: LevelsInfoEnum


class SearchCounter(BaseModel):
    name: str
    offerId: str
    complete: bool
    pointProgress: int
    pointProgressMax: int
    description: str

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
    # `root` is needed to parse automatically `Date` keys, since they are dynamic
    # Minimum 2 items (daily set for today and tomorrow),
    # but occasionally 3 items are available (yesterday, today, tomorrow)
    root: Dict[Date, List[Promotion]] = Field(min_length=2, max_length=3)  # type: ignore

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    def _keys(self) -> List[str]:
        """
        Returns the keys found for storing the DailySets.
        """

        return list(self.root.keys())

    def get_daily_set_for_today(self) -> List[Promotion]:
        """
        Returns the daily set that is available today.
        """

        keys = self._keys()
        if len(keys) == 2:
            key = keys[0]
        elif len(keys) == 3:
            key = keys[1]
        else:
            # Pydantic will ensure that we don't have <2 or >3 keys in `root` dict
            raise RuntimeError("Unreachable")

        return self.root[key]

    def get_daily_set_for_yesterday(self) -> Optional[List[Promotion]]:
        """
        Returns the daily set that was available yesterday.

        Returns None if this set is not found.
        """

        keys = self._keys()
        if len(keys) == 2:
            return None
        elif len(keys) == 3:
            key = keys[0]
        else:
            # Pydantic will ensure that we don't have <2 or >3 keys in `root` dict
            raise RuntimeError("Unreachable")

        return self.root[key]

    def get_daily_set_for_tomorrow(self) -> List[Promotion]:
        """
        Returns the daily set that will be available tomorrow.
        """

        keys = self._keys()
        if len(keys) == 2:
            key = keys[1]
        elif len(keys) == 3:
            key = keys[2]
        else:
            # Pydantic will ensure that we don't have <2 or >3 keys in `root` dict
            raise RuntimeError("Unreachable")

        return self.root[key]


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

        mobile_searches = self.userStatus.counters.mobileSearch
        assert mobile_searches is not None
        mobile_search = mobile_searches[0]
        return mobile_search.get_needed_searches_amount()

    def get_promotions(self) -> List[Promotion]:
        """
        Returns the list of all promotions available in the current dashboard.
        """

        promotions: List[Promotion] = []

        # First, add the daily set promotions,
        # as they have more priority being part of the streak
        today_daily_set = self.dailySetPromotions.get_daily_set_for_today()
        promotions.extend(today_daily_set)

        # Consideration about the daily sets:
        # - Today's is always available to parse and complete.
        # - Tomorrow's is always available to parse, but not to complete.
        # - Yesterday's could be available to parse, but since it doesn't
        #   show up in the Rewards homepage, it is better to not include it
        #   in the parsed promotions.

        # Then add the extra promotions
        promotions.extend(self.morePromotions)

        # Then returns a copy of the list
        return copy.deepcopy(promotions)

    def get_promotional_item(self) -> Optional[Promotion]:
        return self.promotionalItem

    def get_completable_promotions(self) -> List[Promotion]:
        """
        Get the list of all completable promotions in the current dashboard.
        """

        promotions = self.get_promotions()
        completable_promotions = [
            promotion for promotion in promotions if promotion.is_completable()
        ]
        return completable_promotions
