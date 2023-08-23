import datetime
import logging
import smtplib
from email.message import EmailMessage
from enum import Enum
from typing import List, Optional

from attr import define, field

from automsr.config import Config

logger = logging.getLogger(__name__)

NO_SENDER_ERR = "No sender email found!"
NO_SENDER_PSW_ERR = "No sender password found!"
NO_RECIPIENT_ERR = "No recipient specified!"
NO_HOST_ERR = "No SMTP host specified!"
NO_PORT_ERR = "No port specified!"
HOST_NOT_REACHABLE = "Cannot reach host! Check internet connection or hostname."
SHOULD_NOT_CREATE_CONN = "Cannot create Email Connection if should not send any email! Check config settings."


class HtmlColor(Enum):
    """
    Class to map HTML colors to hex values.
    """

    RED = "#FF160D"
    GREEN = "#00D107"


class ExecutionOutcome(Enum):
    """
    Possible outcome for an AutoMSR execution.

    It could be either success or failure.
    """

    FAILURE = "failure"
    SUCCESS = "success"

    def as_color(self) -> HtmlColor:
        """
        Return the object as its Html color representation.

        >>> ExecutionOutcome.FAILURE.as_color() == HtmlColor.RED
        True
        >>> ExecutionOutcome.SUCCESS.as_color() == HtmlColor.GREEN
        True
        """

        if self is self.FAILURE:
            return HtmlColor.RED
        elif self is self.SUCCESS:
            return HtmlColor.GREEN
        else:
            raise NotImplementedError(self)


@define
class ExecutionStatus:
    """
    Status of an execution related to a single profile.
    """

    outcome: ExecutionOutcome
    email: str
    message: str

    def to_plain_message(self) -> str:
        """
        Return a text plain message representing the object.

        >>> ExecutionStatus(
        ...     outcome=ExecutionOutcome.SUCCESS,
        ...     email="foo@bar.com",
        ...     message="Hello world"
        ... ).to_plain_message()
        'foo@bar.com - Outcome: success - Message: Hello world'
        """

        return f"{self.email} - Outcome: {self.outcome.value} - Message: {self.message}"

    def to_html_message(self):
        """
        Return an HTML-rich message representing the object.

        >>> ExecutionStatus(
        ...     outcome=ExecutionOutcome.SUCCESS,
        ...     email="foo@bar.com",
        ...     message="Hello world"
        ... ).to_html_message()
        '<p>foo@bar.com - Outcome: <font color="#00D107">success</font> - Message: Hello world</p>'
        """

        color = self.outcome.as_color().value
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
    statuses: List[ExecutionStatus]
    subject: str = field(
        factory=lambda: f"AutoMSR {datetime.date.today()} Report message"
    )

    def get_message(self) -> EmailMessage:
        """
        Returns a valid Email Message complaint with RFC 5322.

        >>> _message = ExecutionMessage(
        ...     sender="sender@example.com",
        ...     recipient="recipient@example.com",
        ...     statuses=[],
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
        ...         statuses=[],
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
            [status.to_plain_message() for status in self.statuses]
        )
        complete_message_html = "<br>".join(
            [status.to_html_message() for status in self.statuses]
        )

        message.set_content(complete_message_text_plain)
        message.add_alternative(complete_message_html, subtype="html")

        return message


@define(slots=False)
class EmailConnection:
    sender: str
    password: str
    recipient: str
    host: str
    port: int = field(converter=int)
    tls: bool = field(default=False, converter=bool)
    smtp: smtplib.SMTP = field(init=False)

    def open(self) -> None:
        """
        Open an SMTP connection and try to log in with mail server.
        """

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
        logger.info("Message sent!")

    def __enter__(self):
        return self.open()

    def __exit__(self, _):
        self.close()


@define(slots=False)
class OutlookEmailConnection(EmailConnection):
    host: str = "smtp-mail.outlook.com"
    port: int = 587
    tls: bool = True


@define(slots=False)
class GmailEmailConnection(EmailConnection):
    host: str = "smtp.gmail.com"
    port: int = 587
    tls: bool = True


@define
class EmailConnectionFactory:
    """
    Connection factory; will try to create automagically a connection based on the sender address.
    """

    config: Config

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
        >>> factory.get_connection().__class__ is GmailEmailConnection
        True

        >>> _config.email.sender = "foo@outlook.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().__class__ is OutlookEmailConnection
        True

        >>> _config.email.sender = "foo@foobar.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().__class__ is EmailConnection
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
        assert config.recipient is not None

        # Handle Gmail emails
        if domain == "gmail.com":
            logger.debug("Gmail domain found")
            return GmailEmailConnection(
                sender=sender,
                password=config.sender_password.get_secret_value(),
                recipient=config.recipient,
            )

        # Handle Outlook emails
        elif domain.split(".")[0] in ("live", "outlook", "hotmail"):
            logger.debug("Outlook domain found")
            return OutlookEmailConnection(
                sender=sender,
                password=config.sender_password.get_secret_value(),
                recipient=config.recipient,
            )

        # Handle custom domains
        else:
            logger.debug("Custom domain found")
            assert config.host is not None
            assert config.port is not None
            assert config.tls is not None

            return EmailConnection(
                sender=sender,
                password=config.sender_password.get_secret_value(),
                recipient=config.recipient,
                host=config.host,
                port=config.port,
                tls=config.tls,
            )
