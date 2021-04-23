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
    # get options from config
    credentials_fp = config["automsr"]["credentials"]
    headless = config["selenium"]["headless"]

    # overwrite headless kw in kwargs with the
    # actual value passed as keyword arg
    kwargs.update(headless=headless)

    # test if environment is set correctly
    test_environment(**kwargs)

    # check if should skip all credentials
    # placed after test_environment to check
    # for possible env errors

    for credentials in get_safe_credentials(credentials_fp):
        logger.info(f"Working on credentials [email={credentials['email']}]")

        MicrosoftRewards.do_every_activity(credentials=credentials)


if __name__ == "__main__":
    main()
