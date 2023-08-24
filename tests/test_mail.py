import textwrap
import unittest

from automsr.config import Profile
from automsr.datatypes.execution import OutcomeType, Status, Step, StepType
from automsr.mail import StatusMessage


class MailTestCase(unittest.TestCase):
    """
    Base class for Test Cases related to the module `mail`.
    """

    def test_plain_message(self) -> None:
        """
        Test that, given a profile and some steps, the corresponding
        plain message representation matches the expected one.
        """

        expected_message = textwrap.dedent(
            """\
            Email: foo@bar.com
            Overall outcome: FAILURE
            Step GET_DASHBOARD has outcome SUCCESS.
            Step PROMOTIONS has outcome FAILURE. Explanation: Something broke :(
        """
        )

        profile = Profile(email="foo@bar.com", profile="Profile 1")
        steps = [
            Step(outcome=OutcomeType.SUCCESS, type=StepType.GET_DASHBOARD),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.PROMOTIONS,
                explanation="Something broke :(",
            ),
        ]
        status = Status(profile=profile, steps=steps)
        status_message = StatusMessage(status=status)
        message = status_message.to_plain_text()
        self.assertEqual(expected_message, message)

    def test_html_message(self) -> None:
        """
        Test that, given a profile and some steps, the corresponding
        HTML message representation matches the expected one.
        """

        expected_message = textwrap.dedent(
            """\
            <h3>Profile: foo@bar.com</h3>
            <p>Overall outcome: ❌ FAILURE</p>
            <h4>Steps outcome</h4>
            <ul>
            <li><code>GET_DASHBOARD</code>: ✔️ SUCCESS</li>
            <li><code>PROMOTIONS</code>: ❌ FAILURE</li>
            <li>Explanation: Something broke :(</li>
            <li><code>END_SESSION</code>: ❌ FAILURE</li>
            <li>Explanation: Something broke again?!</li>
            </ul>"""
        )

        profile = Profile(email="foo@bar.com", profile="Profile 1")
        steps = [
            Step(outcome=OutcomeType.SUCCESS, type=StepType.GET_DASHBOARD),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.PROMOTIONS,
                explanation="Something broke :(",
            ),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.END_SESSION,
                explanation="Something broke again?!",
            ),
        ]
        status = Status(profile=profile, steps=steps)
        status_message = StatusMessage(status=status)
        message = status_message.to_html()
        self.assertEqual(expected_message, message)
