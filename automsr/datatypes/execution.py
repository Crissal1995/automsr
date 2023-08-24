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

    PROMOTIONS = auto()
    PUNCHCARDS = auto()
    PC_SEARCHES = auto()
    MOBILE_SEARCHES = auto()


@define
class ExecutionStepStatus:
    """
    Status of a single step of an entire execution.
    """

    profile: Profile
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
