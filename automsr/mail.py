import datetime
import logging
import smtplib
from email.message import EmailMessage
from enum import Enum
from typing import Optional

from attr import define, field

from automsr.config import Config

logger = logging.getLogger(__name__)
NO_SENDER_ERR = "No sender email found!"
NO_SENDER_PSW_ERR = "No sender password found!"
NO_RECIPIENT_ERR = "No recipient specified!"
NO_HOST_ERR = "No SMTP host specified!"
NO_PORT_ERR = "No port specified!"
HOST_NOT_REACHABLE = "Cannot reach host! Check internet connection or hostname"
SHOULD_NOT_CREATE_CONN = (
    "Cannot create Email Connection if should not send any email! Check config"
)


class RewardsStatusEnum(Enum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


@define
class RewardsStatus:
    email: str
    status: RewardsStatusEnum
    message: str = ""

    def _set_status_and_message(self, status: RewardsStatusEnum, message: str):
        self.status = status
        self.message = message

    def set_success(self, message: str = ""):
        self._set_status_and_message(RewardsStatusEnum.SUCCESS, message)

    def set_failure(self, message: str = ""):
        self._set_status_and_message(RewardsStatusEnum.FAILURE, message)

    def to_plain(self):
        msg = f"{self.email} - {self.status.value}"
        if self.message:
            msg += f" - {self.message}"
        return msg

    def to_html(self):
        color = "red" if self.status is RewardsStatusEnum.FAILURE else "green"
        msg = f'<p><b>{self.email} - <font color="{color}">{self.status.value}</font></b></p>'
        if self.message:
            msg += f"<p><b>Message:</b> {self.message}</p>"
        return msg


class RewardsEmailMessage(EmailMessage):
    """An email message customized for Auto MSR"""

    now = datetime.date.today()
    prefix = "[AUTOMSR]"

    success_subject = f"{prefix} {now} SUCCESS"
    failure_subject = f"{prefix} {now} FAILURE"

    @classmethod
    def get_message(
        cls,
        from_email: str,
        to_email: str,
        subject: str,
        content: str = "",
        content_html: str = "",
    ):
        msg = cls()

        # setup message
        msg["From"] = from_email
        msg["To"] = to_email

        msg["Subject"] = subject

        msg.set_content(content)
        if content_html:
            msg.add_alternative(content_html, subtype="html")

        return msg

    @classmethod
    def get_success_message(
        cls, from_email: str, to_email: str, content: str = "", content_html: str = ""
    ):
        return cls.get_message(
            from_email=from_email,
            to_email=to_email,
            subject=cls.success_subject,
            content=content,
            content_html=content_html,
        )

    @classmethod
    def get_failure_message(
        cls, from_email: str, to_email: str, content: str = "", content_html: str = ""
    ):
        return cls.get_message(
            from_email=from_email,
            to_email=to_email,
            subject=cls.failure_subject,
            content=content,
            content_html=content_html,
        )


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

    def send_success_message(self):
        msg = RewardsEmailMessage.get_success_message(self.sender, self.recipient)
        self.smtp.send_message(msg)

    def send_failure_message(self):
        msg = RewardsEmailMessage.get_failure_message(self.sender, self.recipient)
        self.smtp.send_message(msg)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
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
        >>> config_path = Path("tests/configs/config.example.yaml")
        >>> _config = Config.from_yaml(config_path)
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().__class__
        <class 'automsr.mail.GmailEmailConnection'>

        >>> _config.email.sender = "foo@outlook.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().__class__
        <class 'automsr.mail.OutlookEmailConnection'>

        >>> _config.email.sender = "foo@foobar.com"
        >>> factory = EmailConnectionFactory(config=_config)
        >>> factory.get_connection().__class__
        <class 'automsr.mail.EmailConnection'>
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
