import logging

from msrewards import MicrosoftRewards
from msrewards.mail import OutlookEmailConnection, RewardsStatus
from msrewards.utility import config, get_safe_credentials, test_environment

FORMAT = "%(asctime)s :: %(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"
formatter = logging.Formatter(FORMAT)

stream_level = logging.DEBUG if config["automsr"]["verbose"] else logging.INFO
stream_handler = logging.StreamHandler()
stream_handler.setLevel(stream_level)

file_handler = logging.FileHandler("main.log")
file_handler.setLevel(logging.INFO)

file_debug_handler = logging.FileHandler("main.debug.log")
file_debug_handler.setLevel(logging.DEBUG)

# set formatters and add handlers to main logger
logger = logging.getLogger("msrewards")
logger.setLevel(logging.DEBUG)

handlers = (stream_handler, file_handler, file_debug_handler)

for handler in handlers:
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main(**kwargs):
    # get credentials filepath from config
    credentials_fp = config["automsr"]["credentials"]

    # hardcoded because it should be 2 at least
    retry = 5

    # test if env is correctly set
    test_environment(**kwargs)

    # if the email is not null or empty string, it will be used
    send_email = bool(config["automsr"]["email"])
    if send_email:
        logger.info(
            "Recipient email found, so emails will be"
            " sent in case of success/failure"
        )
    else:
        logger.info(
            "No recipient email was found, so no email will be"
            " sent in case of success/failure"
        )

    credentials_sender = None
    status_dict = dict()

    # cycle over credentials, getting points from activities
    for i, credentials in enumerate(get_safe_credentials(credentials_fp)):
        # take the first credentials set as only one sender
        if i == 0:
            credentials_sender = credentials

        # if we're iterating over multiple credentials, print a divider
        if i > 0:
            logger.info("-" * 30)

        email = credentials["email"]
        logger.info(f"Working on credentials [email={email}]")

        for j in range(retry):
            try:
                MicrosoftRewards.do_every_activity(credentials=credentials)
            except Exception as e:
                logger.warning(f"An error occurred: {e}")
                logger.debug(e, exc_info=True)
                if j < retry - 1:
                    logger.info("Retrying...")
                else:
                    logger.warning("No more retries!")
                    status_dict[credentials["email"]] = RewardsStatus.FAILURE
            else:
                logger.info(f"Completed execution for {email}")
                status_dict[credentials["email"]] = RewardsStatus.SUCCESS
                break

    # at the end of the cycle, we'll send the email with the report status
    # if credentials_sender is set (there is almost one credentials to work with)
    # and if recipient is set
    if send_email and credentials_sender:
        with OutlookEmailConnection(credentials_sender) as conn:
            conn.send_status_message(status_dict)


if __name__ == "__main__":
    main()
