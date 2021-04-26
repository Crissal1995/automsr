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

    # test if env is correctly set
    test_environment(**kwargs)

    # cycle over credentials, getting points from activities
    for credentials in get_safe_credentials(credentials_fp):
        logger.info(f"Working on credentials [email={credentials['email']}]")
        MicrosoftRewards.do_every_activity(credentials=credentials)


if __name__ == "__main__":
    main()
