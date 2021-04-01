import logging
import pathlib

from msrewards import MicrosoftRewards

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

for fp in pathlib.Path().glob("credentials*.json"):
    logging.info(f"Working on {fp}")
    MicrosoftRewards.daily_routine(credentials_fp=fp)
