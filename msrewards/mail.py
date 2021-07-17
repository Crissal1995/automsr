import datetime
import logging
import smtplib
from email.message import EmailMessage
from enum import Enum
from typing import Dict

from msrewards.utility import config

logger = logging.getLogger(__name__)


class MissingRecipientEmailError(Exception):
    """Error raised when no destination email is found inside config"""


class RewardsStatus(Enum):
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


class RewardsStatusDict:
    status_dict: Dict[str, RewardsStatus] = {}

    def add(self, email: str, status: RewardsStatus):
        if email in self.status_dict:
            raise ValueError(f"Status already found for {email}")
        self.status_dict[email] = status

    def add_failure(self, email: str):
        self.add(email, RewardsStatus.FAILURE)

    def add_success(self, email: str):
        self.add(email, RewardsStatus.SUCCESS)

    def as_dict(self):
        return self.status_dict


class RewardsEmailMessage(EmailMessage):
    """An email message customized for Auto MSR"""

    now = datetime.date.today()
    prefix = "[AUTOMSR]"

    success_subject = f"{prefix} {now} SUCCESS"
    failure_subject = success_subject.replace("SUCCESS", "FAILURE")
    status_subject = success_subject.replace("SUCCESS", "STATUS")

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
    def get_status_message(
        cls, from_email: str, to_email: str, content: str = "", content_html: str = ""
    ):
        return cls.get_message(
            from_email=from_email,
            to_email=to_email,
            subject=cls.status_subject,
            content=content,
            content_html=content_html,
        )

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


class EmailConnection:
    def __init__(
        self,
        credentials: dict,
        host: str,
        port: int,
        ssl: bool = True,
        to_address: str = None,
    ):
        kwargs = dict(host=host, port=port)

        self.from_email = credentials["email"]
        to_email = to_address or config["automsr"]["email"]

        if to_email:
            self.to_email = to_email
        else:
            raise MissingRecipientEmailError()

        # create the smtp connection
        self.smtp = smtplib.SMTP(**kwargs)

        # send an ehlo message to the server
        self.smtp.ehlo()

        # if ssl is enabled, start tls
        if ssl:
            self.smtp.starttls()

        # login with auth credentials
        self.smtp.login(self.from_email, credentials["password"])
        logger.debug("SMTP connection established")

    def _quit(self):
        try:
            self.smtp.quit()
            logger.debug("SMTP connection closed")
        except smtplib.SMTPServerDisconnected:
            logger.debug("SMTP connection was already closed")

    def __del__(self):
        self._quit()

    def _send_message(self, msg: EmailMessage):
        self.smtp.send_message(msg)
        logger.debug("Sent email to specified recipient")

    def send_status_message(self, status_dict: Dict[str, RewardsStatus]):
        content_list = []
        content_html_list = []

        for email, status in status_dict.items():
            success = status is RewardsStatus.SUCCESS
            color = "green" if success else "red"

            content_list.append(f"{email} - {status.value}")
            content_html_list.append(
                f'<p><b>{email} - <font color="{color}">{status.value}</font></b></p>'
            )

        content_html_br = "<br>".join(content_html_list)
        content_html = f"<html><head></head><body>{content_html_br}</body></html>"

        content = "\n".join(content_list)

        msg = RewardsEmailMessage.get_status_message(
            self.from_email, self.to_email, content=content, content_html=content_html
        )
        self._send_message(msg)

    def send_success_message(self):
        msg = RewardsEmailMessage.get_success_message(self.from_email, self.to_email)
        self._send_message(msg)

    def send_failure_message(self):
        msg = RewardsEmailMessage.get_failure_message(self.from_email, self.to_email)
        self._send_message(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._quit()


class OutlookEmailConnection(EmailConnection):
    def __init__(self, credentials: dict, to_address: str = None):
        super().__init__(
            credentials=credentials,
            to_address=to_address,
            host="smtp-mail.outlook.com",
            port=587,
            ssl=True,
        )