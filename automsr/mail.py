import datetime
import logging
import random
import smtplib
from email.message import EmailMessage
from enum import Enum
from typing import Dict, List

import automsr.utility
from automsr.exception import (
    AuthenticationError,
    ConfigurationError,
    EmailError,
    MalformedSenderError,
    MissingRecipientError,
)

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


class RewardsStatus:
    def __init__(self, email: str):
        self.email = email

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
        sender: str = None,
        password: str = None,
        recipient: str = None,
        tls: bool = False,
        host: str = "",
        port: int = 0,
    ):
        self.sender = sender or automsr.utility.config["email"]["sender"]
        self.password = password or automsr.utility.config["email"]["password"]
        self.recipient = recipient or automsr.utility.config["email"]["recipient"]
        self.tls = automsr.utility.config["email"]["tls"] or tls
        self.host = automsr.utility.config["email"]["host"] or host
        self.port = automsr.utility.config["email"]["port"] or port
        self.smtp = smtplib.SMTP(host=self.host, port=self.port)

        if not host:
            raise ConfigurationError(NO_HOST_ERR)

        if not port:
            raise ConfigurationError(NO_PORT_ERR)

        if not self.sender:
            raise MalformedSenderError(NO_SENDER_ERR)

        if not self.password:
            raise MalformedSenderError(NO_SENDER_PSW_ERR)

        if not self.recipient:
            raise MissingRecipientError(NO_RECIPIENT_ERR)

    def open(self):
        try:
            # send an ehlo message to the server
            self.smtp.ehlo()

            # if TLS is enabled, start it
            if self.tls:
                self.smtp.starttls()

            # actual login
            self.smtp.login(self.sender, self.password)

        except smtplib.SMTPAuthenticationError:
            raise AuthenticationError("Invalid credentials provided!")
        except TimeoutError:
            raise EmailError(HOST_NOT_REACHABLE)
        else:
            return self

    def close(self):
        try:
            self.smtp.quit()
        except smtplib.SMTPServerDisconnected:
            pass
        finally:
            logger.debug("SMTP connection closed")

    def __del__(self):
        self.close()

    def _send_message(self, msg: EmailMessage):
        self.smtp.send_message(msg)
        logger.debug("Sent email to specified recipient")

    def send_status_message(self, status_list: List[RewardsStatus]):
        content_list = []
        content_html_list = []

        for status in status_list:
            content_list.append(status.to_plain())
            content_html_list.append(status.to_html())

        content_html_br = "<br>".join(content_html_list)
        content_html = f"<html><head></head><body>{content_html_br}</body></html>"

        content = "\n\n".join(content_list)

        msg = RewardsEmailMessage.get_status_message(
            self.sender, self.recipient, content=content, content_html=content_html
        )
        self._send_message(msg)

    def send_success_message(self):
        msg = RewardsEmailMessage.get_success_message(self.sender, self.recipient)
        self._send_message(msg)

    def send_failure_message(self):
        msg = RewardsEmailMessage.get_failure_message(self.sender, self.recipient)
        self._send_message(msg)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class OutlookEmailConnection(EmailConnection):
    def __init__(self, sender: str = None, password: str = None, recipient: str = None):
        super().__init__(
            host="smtp-mail.outlook.com",
            port=587,
            tls=True,
            sender=sender,
            password=password,
            recipient=recipient,
        )


class GmailEmailConnection(EmailConnection):
    def __init__(self, sender: str = None, password: str = None, recipient: str = None):
        super().__init__(
            host="smtp.gmail.com",
            port=587,
            tls=True,
            sender=sender,
            password=password,
            recipient=recipient,
        )


class EmailConnectionFactory:
    def __init__(self, all_credentials: List[Dict[str, str]]) -> None:
        self.config = automsr.utility.config["email"]
        recipient = self.config["recipient"]
        self.send = self.config["send"]

        if self.send and not recipient:
            raise MissingRecipientError(NO_RECIPIENT_ERR)
        self.credentials = all_credentials

    def _get_connection_from_credentials(self, index: int, recipient: str = None):
        """Return the OutlookEmailConnection corresponding to
        the credentials at position index in the credentials array."""
        creds = self.credentials[index]
        email = creds.get("email")
        password = creds.get("password")
        return OutlookEmailConnection(email, password, recipient)

    def get_connection(self) -> EmailConnection:
        """Return the EmailConnection specified by the chosen strategy.
        If this should not send any email (send=False), raise an error"""

        if not self.send:
            raise ConfigurationError(SHOULD_NOT_CREATE_CONN)

        recipient = self.config["recipient"]

        strategy = self.config["strategy"]
        n = len(self.credentials)

        if strategy == "gmail":
            email = self.config["sender"]
            psw = self.config["password"]
            return GmailEmailConnection(sender=email, password=psw, recipient=recipient)

        elif strategy == "custom":
            email = self.config["sender"]
            psw = self.config["password"]
            host = self.config["host"]
            port = self.config["port"]
            tls = self.config["tls"]
            return EmailConnection(
                host=host,
                port=port,
                sender=email,
                password=psw,
                recipient=recipient,
                tls=tls,
            )

        else:
            if strategy == "first":
                index = 0
            elif strategy == "last":
                index = n - 1
            elif strategy == "random":
                index = random.randint(0, n - 1)
            else:
                raise NotImplementedError
            return self._get_connection_from_credentials(index, recipient)
