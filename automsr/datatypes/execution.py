from enum import Enum, auto
from typing import List

from attr import define

from automsr.config import Profile


class ExecutionOutcome(Enum):
    """
    Possible outcome for an execution.
    """

    FAILURE = "failure"
    SUCCESS = "success"


class ExecutionStep(Enum):
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
    def get_ordered_steps(cls) -> List["ExecutionStep"]:
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
class ExecutionStepStatus:
    """
    Status of a single step of an entire execution.
    """

    step: ExecutionStep
    outcome: ExecutionOutcome


@define
class ExecutionStatus:
    """
    Status of the whole execution for a profile.
    """

    profile: Profile
    steps: List[ExecutionStepStatus]

    def get_outcome(self) -> ExecutionOutcome:
        """
        Find the overall outcome based on the outcome of the children steps.
        """

        outcomes = [step.outcome for step in self.steps]

        if all(outcome is ExecutionOutcome.SUCCESS for outcome in outcomes):
            return ExecutionOutcome.SUCCESS
        else:
            return ExecutionOutcome.FAILURE