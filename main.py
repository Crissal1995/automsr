import datetime
import json
import logging

from msrewards import MicrosoftRewards, exceptions
from msrewards.constants import NAME

FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s"
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
logger = logging.getLogger(NAME)
logger.setLevel(logging.DEBUG)

handlers = (stream_handler, file_handler, file_debug_handler, daily_handler)

for handler in handlers:
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def to_skip(creds: dict):
    """Function utility to know which activity,
    listed as (daily_activities, daily_searches), is
    to be skipped.
    False means the activity should not be skipped,
    True otherwise.
    """
    if not creds.get("skip"):
        return False, False

    # lower() to ensure it's a str
    try:
        skip_str = creds["skip"].lower()
    except AttributeError:
        err = "skip value must be string!"
        logging.error(err)
        raise ValueError(err)

    values = ("activity", "search", "all", "no")
    if skip_str not in values:
        err = f"skip string must be in {values}"
        logging.error(err)
        raise ValueError(err)

    return_dict = {
        "activity": (True, False),
        "search": (False, True),
        "all": (True, True),
        "no": (False, False),
    }
    return return_dict[skip_str]


def main(**kwargs):
    with open("credentials.json") as fp:
        credentials_list = json.load(fp)

    for i, credentials in enumerate(credentials_list):
        logger.info(f"Working on credentials no. {i + 1}")

        skip_activity, skip_searches = to_skip(credentials)

        if not skip_activity:
            logger.info("Start daily activities")
            try:
                MicrosoftRewards.daily_activities(credentials=credentials, **kwargs)
            except (exceptions.WebDriverException, AssertionError) as e:
                logger.error(e)
                logger.error("Cannot complete daily activities")
        else:
            logger.info("Skipping daily activities")

        if not skip_searches:
            logger.info("Start daily searches")
            try:
                MicrosoftRewards.daily_searches(credentials=credentials, **kwargs)
            except exceptions.WebDriverException as e:
                logger.error(e)
                logger.error("Cannot complete daily searches")
        else:
            logger.info("Skipping daily searches")


if __name__ == "__main__":
    main(headless=False)
