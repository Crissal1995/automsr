from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, RootModel, constr

Date = constr(pattern=r"\d{2}/\d{2}/\d{4}")


class LevelsInfoEnum(Enum):
    level_1 = "Level1"
    level_2 = "Level2"


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


class PcSearchCounter(BaseModel):
    name: str
    offerId: str
    complete: bool
    pointProgress: int
    pointProgressMax: int

    def is_completable(self) -> bool:
        return not self.complete


class Counters(BaseModel):
    pcSearch: List[PcSearchCounter]


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
