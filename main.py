import json
import logging

from msrewards import MicrosoftRewards

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("main.log", "w"))
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


with open("credentials.json") as fp:
    credentials_list = json.load(fp)

for i, credentials in enumerate(credentials_list):
    logging.info(f"Working on credentials no. {i + 1}")

    skip_activity, skip_searches = to_skip(credentials)

    if not skip_activity:
        logging.info("Start daily activities")
        MicrosoftRewards.daily_activities(credentials=credentials)
    else:
        logging.info("Skipping daily activities")

    if not skip_searches:
        logging.info("Start daily searches")
        MicrosoftRewards.daily_searches(credentials=credentials)
    else:
        logging.info("Skipping daily searches")
