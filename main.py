import logging

from msrewards import MicrosoftRewards
from msrewards.utility import config, get_safe_credentials, test_environment

FORMAT = "%(asctime)s :: %(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"
formatter = logging.Formatter(FORMAT)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler("main.log")
file_handler.setLevel(logging.INFO)

file_debug_handler = logging.FileHandler("main.debug.log")
file_debug_handler.setLevel(logging.DEBUG)

# set formatters and add handlers to main logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handlers = (stream_handler, file_handler, file_debug_handler)

for handler in handlers:
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main(**kwargs):
    # get credentials filepath from config
    credentials_fp = config["automsr"]["credentials"]

    # get retries from config
    retry = config["automsr"]["retry"]

    # set at least one cycle
    if retry < 1:
        retry = 1

    # test if env is correctly set
    test_environment(**kwargs)

    # cycle over credentials, getting points from activities
    for i, credentials in enumerate(get_safe_credentials(credentials_fp)):
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
            else:
                logger.info(f"Completed execution for {email}")
                break


if __name__ == "__main__":
    main()
