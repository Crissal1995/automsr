import datetime
import logging

from msrewards import MicrosoftRewards
from msrewards.utility import get_safe_credentials, test_environment

FORMAT = "%(asctime)s :: %(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"
formatter = logging.Formatter(FORMAT)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler("main.log")
file_handler.setLevel(logging.INFO)

file_debug_handler = logging.FileHandler("main.debug.log")
file_debug_handler.setLevel(logging.DEBUG)

now = datetime.date.today()
fh = f"{now.isoformat()}.log"
daily_handler = logging.FileHandler(fh)
daily_handler.setLevel(logging.DEBUG)

# set formatters and add handlers to main logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handlers = (stream_handler, file_handler, file_debug_handler, daily_handler)

for handler in handlers:
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def main(credentials_fp="credentials.json", *, headless: bool, **kwargs):
    # overwrite headless kw in kwargs with the
    # actual value passed as keyword arg
    kwargs.update(headless=headless)

    # test if environment is set correctly
    test_environment(**kwargs)

    for credentials in get_safe_credentials(credentials_fp):
        logger.info(f"Working on credentials [email={credentials['email']}]")

        skip_activity = credentials["skip_activity"]
        skip_search = credentials["skip_search"]

        if not skip_activity:
            logger.info("Start daily activities")
            try:
                MicrosoftRewards.daily_activities(credentials=credentials, **kwargs)
            except Exception as e:
                logger.error(f"Cannot complete daily activities - error: {e}")
        else:
            logger.info("Skipping daily activities")

        if not skip_search:
            logger.info("Start daily searches")
            try:
                MicrosoftRewards.daily_searches(credentials=credentials, **kwargs)
            except Exception as e:
                logger.error(f"Cannot complete daily searches - error: {e}")
        else:
            logger.info("Skipping daily searches")


if __name__ == "__main__":
    main(headless=True)
