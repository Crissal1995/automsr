import datetime
import logging
import random
import smtplib
from email.message import EmailMessage
from enum import Enum
from typing import List, Optional

from attr import define, field

from automsr.config import Config
from automsr.datatypes.execution import ExecutionOutcome, ExecutionStatus

logger = logging.getLogger(__name__)


class HtmlColor(Enum):
    """
    Class to map HTML colors to hex values.
    """

    RED = "#FF160D"
    GREEN = "#00D107"

    @classmethod
    def from_outcome(cls, outcome: ExecutionOutcome) -> "HtmlColor":
        """
        Given an input outcome, return the corresponding html color representation.

        >>> HtmlColor.from_outcome(ExecutionOutcome.FAILURE) is HtmlColor.RED
        True
        >>> HtmlColor.from_outcome(ExecutionOutcome.SUCCESS) is HtmlColor.GREEN
        True
        """

        if outcome is ExecutionOutcome.FAILURE:
            return HtmlColor.RED
        elif outcome is ExecutionOutcome.SUCCESS:
            return HtmlColor.GREEN
        else:
            raise NotImplementedError(outcome)


@define
class ExecutionStatusMessage:
    """
    Wrapper for an ExecutionStatus object to make it messages-aware.
    """

    outcome: ExecutionOutcome
    email: str
    message: str

    @classmethod
    def from_execution_status(cls, status: ExecutionStatus) -> "ExecutionStatusMessage":
        """
        Parse an Execution Status object and returns a wrapper capable of generating
        email messages from it.

        >>> from automsr.config import Profile
        >>> from automsr.datatypes.execution import ExecutionStepStatus, ExecutionStatus, ExecutionStep
        >>> profile = Profile(email="foo@bar.com", profile="Profile 1")
        >>> steps = [
        ...     ExecutionStepStatus(step=ExecutionStep.PROMOTIONS, outcome=ExecutionOutcome.SUCCESS),
        ...     ExecutionStepStatus(step=ExecutionStep.PUNCHCARDS, outcome=ExecutionOutcome.FAILURE, explanation="This is an explanation."),
        ... ]
        >>> execution_status = ExecutionStatus(profile=profile, steps=steps)
        >>> status_message = ExecutionStatusMessage.from_execution_status(status=execution_status)
        >>> status_message.to_plain_message()
        'foo@bar.com - Outcome: failure - Message: 1) PROMOTIONS - outcome: success. 2) PUNCHCARDS - outcome: failure - explanation: This is an explanation.'
        >>> status_message.to_html_message()
        '<p>foo@bar.com - Outcome: <font color="#FF160D">failure</font> - Message: 1) PROMOTIONS - outcome: success. 2) PUNCHCARDS - outcome: failure - explanation: This is an explanation.</p>'
        """  # noqa: E501

        outcome = status.get_outcome()
        email = status.profile.email
        message = status.get_message()

        return cls(outcome=outcome, email=email, message=message)

    def to_plain_message(self) -> str:
        """
        Return a text plain message representing the object.

        >>> ExecutionStatusMessage(
        ...     outcome=ExecutionOutcome.SUCCESS,
        ...     email="foo@bar.com",
        ...     message="Hello world"
        ... ).to_plain_message()
        'foo@bar.com - Outcome: success - Message: Hello world'
        """

        return f"{self.email} - Outcome: {self.outcome.value} - Message: {self.message}"

    def to_html_message(self) -> str:
        """
        Return an HTML-rich message representing the object.

        >>> ExecutionStatusMessage(
        ...     outcome=ExecutionOutcome.SUCCESS,
        ...     email="foo@bar.com",
        ...     message="Hello world"
        ... ).to_html_message()
        '<p>foo@bar.com - Outcome: <font color="#00D107">success</font> - Message: Hello world</p>'
        """

        color: str = HtmlColor.from_outcome(outcome=self.outcome).value
        message = " - ".join(
            [
                f"{self.email}",
                f'Outcome: <font color="{color}">{self.outcome.value}</font>',
                f"Message: {self.message}",
            ]
        )
        complete_message = f"<p>{message}</p>"
        return complete_message


@define
class ExecutionMessage:
    """
    Email message wrapper, customized for the tool logic.
    """

    sender: str
    recipient: str
    status_messages: List[ExecutionStatusMessage]
    subject: str = field(
        factory=lambda: f"AutoMSR {datetime.date.today()} Report message"
    )

    def get_message(self) -> EmailMessage:
        """
        Returns a valid Email Message complaint with RFC 5322.

        >>> _message = ExecutionMessage(
        ...     sender="sender@example.com",
        ...     recipient="recipient@example.com",
        ...     status_messages=[],
        ...     subject="My Subject",
        ... ).get_message()
        >>> print(_message.as_string())  # doctest: +ELLIPSIS
        From: sender@example.com
        To: recipient@example.com
        Subject: My Subject
        MIME-Version: 1.0
        ...

        >>> from unittest.mock import patch
        >>> with patch("mail.datetime", wraps=datetime) as mock:
        ...     mock.date.today.return_value = "2023-01-01"
        ...     _message = ExecutionMessage(
        ...         sender="sender@example.com",
        ...         recipient="recipient@example.com",
        ...         status_messages=[],
        ...     ).get_message()
        ...     print(_message.as_string())  # doctest: +ELLIPSIS
        From: sender@example.com
        To: recipient@example.com
        Subject: AutoMSR 2023-01-01 Report message
        MIME-Version: 1.0
        ...
        """

        message = EmailMessage()

        message.add_header("From", self.sender)
        message.add_header("To", self.recipient)
        message.add_header("Subject", self.subject)

        complete_message_text_plain = "\n\n".join(
            [message.to_plain_message() for message in self.status_messages]
        )
        complete_message_html = "<br>".join(
            [message.to_html_message() for message in self.status_messages]
        )

        message.set_content(complete_message_text_plain)
        message.add_alternative(complete_message_html, subtype="html")

        return message


@define
class EmailConnection:
    sender: str
    password: str
    host: str
    port: int = field(converter=int)
    tls: bool = field(default=False, converter=bool)
    smtp: smtplib.SMTP = field(init=False)

    def open(self) -> None:
        """
        Open an SMTP connection and try to log in with mail server.
        """

        self.smtp = smtplib.SMTP(host=self.host, port=self.port)
        self.smtp.ehlo()
        if self.tls:
            self.smtp.starttls()
        self.smtp.login(self.sender, self.password)

    def close(self) -> None:
        """
        Closes an SMTP established connection.
        """

        try:
            self.smtp.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        finally:
            logger.debug("SMTP connection closed")

    def test_connection(self) -> None:
        """
        Test if the provided connection is successful.
        Any exception is raised to the caller.
        """

        self.open()
        self.close()
        logger.info("Email connection was successful")

    def send_message(self, message: ExecutionMessage) -> None:
        """
        Send a Message using the provided credentials and SMTP.
        """
        smtp_message = message.get_message()
        self.smtp.send_message(msg=smtp_message)
        logger.debug("Message sent correctly with smtp!")

    def __enter__(self):
        return self.open()

    def __exit__(self, _exc_type, _exc_value, _traceback):
        # Check docs for more info on these parameters:
        # https://docs.python.org/3/reference/datamodel.html#object.__exit__
        self.close()


@define
class EmailConnectionFactory:
    """
    Connection factory; will try to create automagically a connection based on the sender address.
    """

    config: Config

    gmail_host = "smtp.gmail.com"
    gmail_port = 587
    gmail_tls = True

    outlook_host = "smtp-mail.outlook.com"
    outlook_port = 587
    outlook_tls = True

    def get_connection(self) -> Optional[EmailConnection]:
        """
        Get an email connection based on the config.

        >>> from pathlib import Path
        >>> current_path = Path(__file__)
        >>> tests_path = current_path.parent.parent / "tests"
        >>> config_path = tests_path / "configs/config.example.yaml"
        >>> _config = Config.from_yaml(config_path)

        >>> _config.email.sender = "foo@gmail.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().host == EmailConnectionFactory.gmail_host
        True

        >>> _config.email.sender = "foo@outlook.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().host == EmailConnectionFactory.outlook_host
        True

        >>> _config.email.sender = "foo@foobar.com"
        >>> _config.email.host = "smtp.foobar.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().host == "smtp.foobar.com"
        True

        >>> _config.email.enable = False
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection() is None
        True
        """

        config = self.config.email

        if not config.enable:
            logger.info("Email send was disabled by config")
            return None

        sender = config.sender
        assert sender is not None
        domain = sender.split("@")[1]
        logger.debug("Sender domain: %s", domain)

        assert config.sender_password is not None
        password = config.sender_password.get_secret_value()

        # Handle Gmail emails
        if domain == "gmail.com":
            logger.debug("Gmail domain found")
            return EmailConnection(
                sender=sender,
                password=password,
                host=self.gmail_host,
                port=self.gmail_port,
                tls=self.gmail_tls,
            )

        # Handle Outlook emails
        elif domain.split(".")[0] in ("live", "outlook", "hotmail"):
            logger.debug("Outlook domain found")
            return EmailConnection(
                sender=sender,
                password=password,
                host=self.outlook_host,
                port=self.outlook_port,
                tls=self.outlook_tls,
            )

        # Handle custom domains
        else:
            logger.debug("Custom domain found")
            assert config.host is not None
            assert config.port is not None
            assert config.tls is not None

            return EmailConnection(
                sender=sender,
                password=password,
                host=config.host,
                port=config.port,
                tls=config.tls,
            )

    def get_connection_strict(self) -> EmailConnection:
        """
        Get an Email Connection, or raise if it would be null.
        """

        connection = self.get_connection()
        if connection is None:
            raise ValueError(
                "Connection is null! Probably you must set `email/enable: true` in your config file."
            )
        return connection


@define
class EmailExecutor:
    config: Config

    def are_messages_enabled(self) -> bool:
        """
        Return whether the email messages are enabled, so that:
        - `email/enable` is `true` in config file;
        - `email/recipient` is a valid non-null string;
        - an email connection can be established with sender's SMTP server
        """

        if not self.config.email.enable:
            return False

        if not self.config.email.recipient:
            return False

        factory = EmailConnectionFactory(config=self.config)
        connection = factory.get_connection_strict()
        try:
            connection.test_connection()
        except smtplib.SMTPException:
            return False
        else:
            return True

    def send_message(self, statuses: List[ExecutionStatusMessage]) -> None:
        """
        Send a message with the content of object's `statuses`.

        Assumes that messages are enabled for the current session.
        """

        recipient: Optional[str] = self.config.email.recipient
        assert recipient is not None

        connection: EmailConnection = EmailConnectionFactory(
            config=self.config
        ).get_connection_strict()
        with connection:
            message = ExecutionMessage(
                sender=connection.sender,
                recipient=recipient,
                status_messages=statuses,
            )
            connection.send_message(message=message)
            logger.info("Message sent correctly!")

    def send_mock_message(self, *, seed: int = 0) -> None:
        """
        Send a mock message in order to make the
        message display something relevant for the user.
        """

        random.seed(seed)

        statuses: List[ExecutionStatusMessage] = []
        for profile in self.config.automsr.profiles:
            email_address = profile.email
            outcome = random.choice(list(ExecutionOutcome))
            message = "Mock result."

            status = ExecutionStatusMessage(
                outcome=outcome,
                email=email_address,
                message=message,
            )
            statuses.append(status)

        logger.info("Mock message sending...")
        self.send_message(statuses=statuses)
