from enum import Enum


class RewardsType(Enum):
    """
    Enum model of possible Rewards type.

    This model is different from `PromotionType`, since that is related to how Rewards handle
    internally the different task/items.

    This is a logic representation at tool level.
    """

    ACTIVITY = "activity"
    SEARCH = "search"
    PUNCHCARD = "punchcard"
