import smtplib
import textwrap
import unittest
from datetime import timedelta
from typing import cast
from unittest.mock import MagicMock, Mock, patch

from automsr.config import Profile
from automsr.datatypes.execution import OutcomeType, Status, Step, StepType
from automsr.mail import EmailConnection, StatusMessage


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
            Points: 12,345
            Overall outcome: FAILURE
            Step GET_DASHBOARD has outcome SUCCESS.
            Step PROMOTIONS has outcome FAILURE. Duration: 0:02:03. Explanation: Something broke :(
        """
        )

        profile = Profile(email="foo@bar.com", profile="Profile 1")
        points = 12345
        steps = [
            Step(outcome=OutcomeType.SUCCESS, type=StepType.GET_DASHBOARD),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.PROMOTIONS,
                explanation="Something broke :(",
                duration=timedelta(seconds=123),
            ),
        ]
        status = Status(profile=profile, steps=steps, points=points)
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
            <p><strong>Points: N/A</strong></p>
            <p><strong>Overall outcome: ❌ FAILURE</strong></p>
            <table>
            <thead>
            <tr>
            <th style="text-align: center;">Outcome</th>
            <th style="text-align: left;">Step</th>
            <th style="text-align: left;">Duration</th>
            <th style="text-align: left;">Explanation</th>
            </tr>
            </thead>
            <tbody>
            <tr>
            <td style="text-align: center;">✔️</td>
            <td style="text-align: left;">GET_DASHBOARD</td>
            <td style="text-align: left;">N/A</td>
            <td style="text-align: left;"></td>
            </tr>
            <tr>
            <td style="text-align: center;">❌</td>
            <td style="text-align: left;">PROMOTIONS</td>
            <td style="text-align: left;">0:00:44</td>
            <td style="text-align: left;">Something broke :(</td>
            </tr>
            <tr>
            <td style="text-align: center;">❌</td>
            <td style="text-align: left;">END_SESSION</td>
            <td style="text-align: left;">0:00:55</td>
            <td style="text-align: left;">Something broke again?!</td>
            </tr>
            </tbody>
            </table>"""
        )

        profile = Profile(email="foo@bar.com", profile="Profile 1")
        points = None
        steps = [
            Step(outcome=OutcomeType.SUCCESS, type=StepType.GET_DASHBOARD),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.PROMOTIONS,
                explanation="Something broke :(",
                duration=timedelta(seconds=44),
            ),
            Step(
                outcome=OutcomeType.FAILURE,
                type=StepType.END_SESSION,
                explanation="Something broke again?!",
                duration=timedelta(seconds=55),
            ),
        ]
        status = Status(profile=profile, steps=steps, points=points)
        status_message = StatusMessage(status=status)
        message = status_message.to_html()
        self.assertEqual(expected_message, message)


class ConnectionTestCase(unittest.TestCase):
    """
    Base class for tests related to connection test cases.
    """

    @patch("smtplib.SMTP")
    def test_get_connection(self, _smtp_mock: MagicMock) -> None:
        connection = EmailConnection(
            sender="user1@foo.com",
            password="super-strong-password",
            host="smtp.foo.com",
            port=123,
            tls=True,
        )

        # good weather scenario: smtp.close() didn't raise
        with connection.open_smtp_connection() as smtp_mock:
            pass
        cast(MagicMock, smtp_mock).close.assert_called_once()

    @patch("smtplib.SMTP")
    def test_get_connection_with_exception(self, _smtp_mock: MagicMock) -> None:
        connection = EmailConnection(
            sender="user1@foo.com",
            password="super-strong-password",
            host="smtp.foo.com",
            port=123,
            tls=True,
        )

        # bad weather scenario: smtp.close() raised
        with connection.open_smtp_connection() as smtp_mock:
            cast(
                MagicMock, smtp_mock
            ).close.side_effect = smtplib.SMTPServerDisconnected
        cast(MagicMock, smtp_mock).close.assert_called_once()

        with self.assertRaises(smtplib.SMTPServerDisconnected):
            smtp_mock.close()

    @patch("smtplib.SMTP")
    @patch.object(EmailConnection, "open_smtp_connection")
    def test_send_message(self, conn_mock: MagicMock, smtp_mock: MagicMock) -> None:
        conn_mock.return_value.__enter__.return_value = smtp_mock

        connection = EmailConnection(
            sender="user1@foo.com",
            password="super-strong-password",
            host="smtp.foo.com",
            port=123,
            tls=True,
        )
        connection.send_message(message=Mock())
