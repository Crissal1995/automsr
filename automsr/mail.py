import datetime
import logging
import random
import smtplib
from email.message import EmailMessage
from typing import Dict, List, Optional

import markdown
from attr import define, field
from faker import Faker  # type: ignore

from automsr.config import Config
from automsr.datatypes.execution import OutcomeType, Status, Step, StepType

logger = logging.getLogger(__name__)


@define
class StatusMessage:
    """
    Wrapper for a status object to make it messages-aware.
    """

    status: Status

    @property
    def email(self) -> str:
        """
        Email address related to this object.
        """

        return self.status.profile.email

    def to_plain_text(self) -> str:
        """
        Return a plain-text representation of the status.
        """

        retval: List[str] = [
            f"Email: {self.email}",
            f"Overall outcome: {self.status.get_outcome().name}",
        ]

        steps = self.status.steps
        for step in steps:
            line = f"Step {step.type.name} has outcome {step.outcome.name}."
            if step.duration:
                line += f" Duration: {step.duration}."
            if step.explanation:
                line += f" Explanation: {step.explanation}"
            retval.append(line)

        message = "\n".join(retval)
        message += "\n"  # add a final newline character
        return message

    def to_markdown(self) -> str:
        """
        Return a Markdown representation of the status.
        """

        status_emojis: Dict[OutcomeType, str] = {
            OutcomeType.SUCCESS: "✔️",
            OutcomeType.FAILURE: "❌",
            OutcomeType.SKIPPED: "⏭️",
        }

        overall_outcome = self.status.get_outcome()
        overall_outcome_emoji = status_emojis[overall_outcome]

        retval: List[str] = [
            f"### Profile: {self.email}",
            f"**Overall outcome: {overall_outcome_emoji} {overall_outcome.name}**",
            # Table creation
            "",
            "| Outcome | Step | Duration | Explanation |",
            "| :---: | :--- | :--- | :--- |",
        ]

        for step in self.status.steps:
            outcome_emoji = status_emojis[step.outcome]
            explanation = step.explanation or ""
            duration = step.duration or "N/A"
            line = (
                f"| {outcome_emoji} | {step.type.name} | {duration} | {explanation} |"
            )
            retval.append(line)

        return "\n".join(retval)

    def to_html(self) -> str:
        """
        Return an HTML representation of the status.
        """

        return markdown.markdown(text=self.to_markdown(), extensions=["extra"])


@define
class ExecutionMessage:
    """
    Email message wrapper, customized for the tool logic.
    """

    sender: str
    recipient: str
    status_messages: List[StatusMessage]
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
        >>> with patch("automsr.mail.datetime", wraps=datetime) as mock:
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

        complete_message_plain_text = "\n\n".join(
            [message.to_plain_text() for message in self.status_messages]
        )
        complete_message_html = "<br>".join(
            [message.to_html() for message in self.status_messages]
        )

        message.set_content(complete_message_plain_text)
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

        connection = factory.get_connection()
        if not connection:
            return False

        try:
            connection.test_connection()
        except smtplib.SMTPException:
            return False
        else:
            return True

    def send_message(
        self, statuses: List[Status], *, subject: Optional[str] = None
    ) -> None:
        """
        Send a message with the content of object's `statuses`.

        It is also possible to change the subject of the message
        providing a non-null `subject`.

        Assumes that messages are enabled for the current session.
        """

        recipient: Optional[str] = self.config.email.recipient
        assert recipient is not None

        status_messages = [StatusMessage(status=status) for status in statuses]

        connection: EmailConnection = EmailConnectionFactory(
            config=self.config
        ).get_connection_strict()
        with connection:
            message = ExecutionMessage(
                sender=connection.sender,
                recipient=recipient,
                status_messages=status_messages,
            )
            if subject is not None:
                message.subject = subject
            connection.send_message(message=message)
            logger.info("Message sent correctly!")

    def send_mock_message(self, *, seed: int = 0) -> None:
        """
        Send a mock message in order to make the
        message display something relevant for the user.
        """

        random.seed(seed)

        fake = Faker(locale="en-US")
        fake.seed_instance(seed)

        statuses: List[Status] = []
        for profile in self.config.automsr.profiles:
            steps: List[Step] = []

            step_types: List[StepType] = StepType.get_ordered_steps()

            for step_type in step_types:
                if profile.skip:
                    outcome = OutcomeType.SKIPPED
                else:
                    outcome = random.choice(list(OutcomeType))

                if outcome is OutcomeType.SUCCESS:
                    explanation = None
                else:
                    explanation = fake.sentence(nb_words=4)

                if outcome is OutcomeType.SKIPPED:
                    duration = None
                else:
                    seconds = fake.random_number(digits=3, fix_len=True)
                    duration = datetime.timedelta(seconds=seconds)

                step = Step(
                    type=step_type,
                    outcome=outcome,
                    explanation=explanation,
                    duration=duration,
                )
                steps.append(step)

            status = Status(profile=profile, steps=steps)
            statuses.append(status)

        logger.info("Sending mock message...")
        self.send_message(statuses=statuses, subject="AutoMSR Mock Report message")
