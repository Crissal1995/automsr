import json
import logging

from msrewards import MicrosoftRewards, exceptions

logger = logging.getLogger()

FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s"
formatter = logging.Formatter(FORMAT)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler("main.log")
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logger.setLevel(logging.INFO)


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


def main():
    with open("credentials.json") as fp:
        credentials_list = json.load(fp)

    for i, credentials in enumerate(credentials_list):
        logging.info(f"Working on credentials no. {i + 1}")

        skip_activity, skip_searches = to_skip(credentials)

        if not skip_activity:
            logging.info("Start daily activities")
            try:
                MicrosoftRewards.daily_activities(credentials=credentials)
            except (exceptions.WebDriverException, AssertionError) as e:
                logging.error(e)
                logging.error("Cannot complete daily activities")
        else:
            logging.info("Skipping daily activities")

        if not skip_searches:
            logging.info("Start daily searches")
            try:
                MicrosoftRewards.daily_searches(credentials=credentials)
            except exceptions.WebDriverException as e:
                logging.error(e)
                logging.error("Cannot complete daily searches")
        else:
            logging.info("Skipping daily searches")


if __name__ == "__main__":
    main()
