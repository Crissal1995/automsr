import logging
from datetime import timedelta
from enum import Enum, auto
from typing import List, Optional

from attr import define

from automsr.config import Profile

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """
    Possible outcome for an execution.
    """

    FAILURE = "failure"
    SUCCESS = "success"
    SKIPPED = "skipped"


class StepType(Enum):
    """
    Type of execution step found during the normal execution.
    """

    START_SESSION = auto()
    GET_DASHBOARD = auto()
    PUNCHCARDS = auto()
    PROMOTIONS = auto()
    PC_SEARCHES = auto()
    MOBILE_SEARCHES = auto()
    END_SESSION = auto()

    @classmethod
    def get_ordered_steps(cls) -> List["StepType"]:
        """
        Returns the step ordered as expected by the `run` flow.
        """

        return [
            # start the session
            cls.START_SESSION,
            # retrieve the dashboard
            cls.GET_DASHBOARD,
            # complete the punchcards, if any
            cls.PUNCHCARDS,
            # complete the promotions, including daily
            cls.PROMOTIONS,
            # complete searches
            cls.PC_SEARCHES,
            cls.MOBILE_SEARCHES,
            # end the session
            cls.END_SESSION,
        ]


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

    def get_outcome(self) -> OutcomeType:
        """
        Find the overall outcome based on the outcome of the children steps.

        >>> from unittest.mock import ANY
        >>> profile = Profile(email="foo@bar.com", profile="profile 1")
        >>> success = Step(type=ANY, outcome=OutcomeType.SUCCESS)
        >>> failure = Step(type=ANY, outcome=OutcomeType.FAILURE)
        >>> skipped = Step(type=ANY, outcome=OutcomeType.SKIPPED)

        >>> Status(profile=profile, steps=[]).get_outcome().name
        'SKIPPED'
        >>> Status(profile=profile, steps=[success]).get_outcome().name
        'SUCCESS'
        >>> Status(profile=profile, steps=[success, skipped]).get_outcome().name
        'SUCCESS'
        >>> Status(profile=profile, steps=[skipped, skipped]).get_outcome().name
        'SKIPPED'
        >>> Status(profile=profile, steps=[skipped, skipped, failure]).get_outcome().name
        'FAILURE'
        """

        outcomes = [step.outcome for step in self.steps]

        # If no step is present, the status defaults to SKIPPED.
        if not outcomes:
            return OutcomeType.SKIPPED

        # The outcome is SKIPPED if all the outcomes are SKIPPED.
        if all(outcome is OutcomeType.SKIPPED for outcome in outcomes):
            return OutcomeType.SKIPPED

        # The outcome is SUCCESS if no outcome is FAILURE,
        # so they are either SUCCESS or SKIPPED.
        if not any(outcome is OutcomeType.FAILURE for outcome in outcomes):
            return OutcomeType.SUCCESS

        # If we are here, at least one outcome is FAILURE.
        return OutcomeType.FAILURE
