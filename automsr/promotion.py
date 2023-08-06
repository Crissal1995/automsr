from enum import Enum

from pydantic import BaseModel


class PromotionType(Enum):
    URL_REWARD = "urlreward"
    QUIZ = "quiz"

    SEARCH = "search"  # PC Search
    EMPTY = ""  # prevents enum casting to fail in case of empty string

    # streak keepers
    STREAK = "streak"
    STREAK_BONUS = "streakbonus"
    COACH_MARKS = "coachmarks"


class PromotionAttributes(BaseModel):
    daily_set_date: str
    description: str
    destination: str
    link_text: str
    max: str
    offerid: str
    progress: str
    sc_bg_image: str
    sc_bg_large_image: str
    small_image: str
    state: str
    title: str
    type: str
    give_eligible: str


class Promotion(BaseModel):
    name: str
    priority: int
    # attributes: PromotionAttributes
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
    smallImageUrl: str
    backgroundImageUrl: str
    promotionBackgroundLeft: str
    promotionBackgroundRight: str
    iconUrl: str
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
