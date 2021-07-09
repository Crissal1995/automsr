import datetime
import logging
import smtplib
from email.message import EmailMessage

from msrewards.utility import config


class MissingRecipientEmailError(Exception):
    """Error raised when no destination email is found inside config"""


class RewardsEmailMessage(EmailMessage):
    """An email message customized for Auto MSR"""

    now = datetime.date.today()
    prefix = "[AUTOMSR]"

    success_subject = f"{prefix} {now} SUCCESS"
    failure_subject = success_subject.replace("SUCCESS", "FAILURE")

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
    def get_success_message(cls, from_email: str, to_email: str, content: str = ""):
        return cls.get_message(
            from_email=from_email,
            to_email=to_email,
            subject=cls.success_subject,
            content=content,
        )

    @classmethod
    def get_failure_message(cls, from_email: str, to_email: str, content: str = ""):
        return cls.get_message(
            from_email=from_email,
            to_email=to_email,
            subject=cls.failure_subject,
            content=content,
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
        logging.info("SMTP connection established")

    def _send_message(self, msg: EmailMessage):
        self.smtp.send_message(msg)
        logging.info("Sent email to specified recipient")

    def send_success_message(self):
        msg = RewardsEmailMessage.get_success_message(self.from_email, self.to_email)
        self._send_message(msg)

    def send_failure_message(self):
        msg = RewardsEmailMessage.get_failure_message(self.from_email, self.to_email)
        self._send_message(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.smtp.quit()


class OutlookEmailConnection(EmailConnection):
    def __init__(self, credentials: dict, to_address: str = None):
        super().__init__(
            credentials=credentials,
            to_address=to_address,
            host="smtp-mail.outlook.com",
            port=587,
            ssl=True,
        )
