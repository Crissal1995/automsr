import json
import logging

from msrewards import MicrosoftRewards

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("main.log", "w"))
logger.setLevel(logging.INFO)

with open("credentials.json") as fp:
    credentials_list = json.load(fp)

for i, credentials in enumerate(credentials_list):
    logging.info(f"Working on credentials no. {i + 1}")
    # MicrosoftRewards.daily_activities(credentials=credentials)
    MicrosoftRewards.daily_searches(credentials=credentials)
