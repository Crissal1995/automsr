import logging
from datetime import timedelta
from enum import Enum, auto
from typing import List, Optional, Set

from attr import define

from automsr.config import Profile

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """
    Possible outcome for an execution.
    """

    FAILURE = auto()
    SUCCESS = auto()
    SKIPPED = auto()
    SUSPENDED = auto()


class StepType(Enum):
    """
    Type of execution step found during the normal execution.
    """

    CHECK_SUSPENDED = auto()

    START_SESSION = auto()
    END_SESSION = auto()

    GET_DASHBOARD = auto()
    GET_POINTS = auto()

    PUNCHCARDS = auto()
    PROMOTIONS = auto()
    PC_SEARCHES = auto()
    MOBILE_SEARCHES = auto()

    @classmethod
    def get_run_steps(cls) -> List["StepType"]:
        """
        Returns the step ordered as expected by the `run` flow.
        """

        return [
            # start the session
            cls.START_SESSION,
            # check if the account was suspended
            cls.CHECK_SUSPENDED,
            # retrieve the dashboard
            cls.GET_DASHBOARD,
            # complete the punchcards, if any
            cls.PUNCHCARDS,
            # complete the promotions, including daily
            cls.PROMOTIONS,
            # complete searches
            cls.PC_SEARCHES,
            cls.MOBILE_SEARCHES,
            # retrieve the dashboard again to get updated points
            cls.GET_DASHBOARD,
            # get the total points
            cls.GET_POINTS,
            # end the session
            cls.END_SESSION,
        ]

    @classmethod
    def get_unskippable_steps(cls) -> Set["StepType"]:
        """
        Returns the steps that must be always executed.
        """

        return {cls.START_SESSION, cls.CHECK_SUSPENDED, cls.END_SESSION}


@define
class Step:
    """
    Status of a single step of an entire execution.
    """

    type: StepType
    outcome: OutcomeType
    explanation: Optional[str] = None
    duration: Optional[timedelta] = None


@define
class Status:
    """
    Status of the whole execution for a profile.
    """

    profile: Profile
    steps: List[Step]
    points: Optional[int]

    def get_outcome(self) -> OutcomeType:
        """
        Find the overall outcome based on the outcome of the children steps.

        >>> from unittest.mock import ANY
        >>> profile = Profile(email="foo@bar.com", profile="profile 1")
        >>> success = Step(type=ANY, outcome=OutcomeType.SUCCESS)
        >>> failure = Step(type=ANY, outcome=OutcomeType.FAILURE)
        >>> skipped = Step(type=ANY, outcome=OutcomeType.SKIPPED)
        >>> suspended = Step(type=ANY, outcome=OutcomeType.SUSPENDED)

        >>> Status(profile=profile, steps=[], points=None).get_outcome().name
        'SKIPPED'
        >>> Status(profile=profile, steps=[success], points=None).get_outcome().name
        'SUCCESS'
        >>> Status(profile=profile, steps=[success, skipped], points=None).get_outcome().name
        'SUCCESS'
        >>> Status(profile=profile, steps=[skipped, skipped], points=None).get_outcome().name
        'SKIPPED'
        >>> Status(profile=profile, steps=[skipped, skipped, failure], points=None).get_outcome().name
        'FAILURE'
        >>> Status(profile=profile, steps=[skipped, skipped, suspended], points=None).get_outcome().name
        'SUSPENDED'
        """

        outcomes = [step.outcome for step in self.steps]
        set_outcomes = set(outcomes)

        # If no step is present, the status defaults to SKIPPED.
        if not set_outcomes:
            return OutcomeType.SKIPPED

        # The outcome is SKIPPED if all the outcomes are SKIPPED.
        if len(set_outcomes) == 1 and OutcomeType.SKIPPED in set_outcomes:
            return OutcomeType.SKIPPED

        # If any outcome is SUSPENDED, the overall outcome is such.
        if OutcomeType.SUSPENDED in set_outcomes:
            return OutcomeType.SUSPENDED

        # If any outcome is FAILURE, the overall outcome is such.
        if OutcomeType.FAILURE in set_outcomes:
            return OutcomeType.FAILURE

        # If we are here, we either have all SUCCESS, or a mix of them and SKIPPED.
        return OutcomeType.SUCCESS
