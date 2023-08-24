import textwrap
import unittest

from automsr.config import Profile
from automsr.datatypes.execution import OutcomeType, Status, Step, StepType
from automsr.mail import StatusMessage


class MailTestCase(unittest.TestCase):
    """
    Base class for Test Cases related to the module `mail`.
    """

    def setUp(self) -> None:
        self.maxDiff = None

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
            <p><strong>Overall outcome: ❌ FAILURE</strong></p>
            <h4>Steps outcome</h4>
            <table>
            <thead>
            <tr>
            <th style="text-align: center;">Step</th>
            <th style="text-align: center;">Outcome</th>
            <th>Explanation</th>
            </tr>
            </thead>
            <tbody>
            <tr>
            <td style="text-align: center;">GET_DASHBOARD</td>
            <td style="text-align: center;">✔️</td>
            <td></td>
            </tr>
            <tr>
            <td style="text-align: center;">PROMOTIONS</td>
            <td style="text-align: center;">❌</td>
            <td>Something broke :(</td>
            </tr>
            <tr>
            <td style="text-align: center;">END_SESSION</td>
            <td style="text-align: center;">❌</td>
            <td>Something broke again?!</td>
            </tr>
            </tbody>
            </table>"""
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
