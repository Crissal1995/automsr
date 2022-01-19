import logging
import sys
from typing import List

import selenium.common.exceptions

import automsr.utility
from automsr import MicrosoftRewards
from automsr.mail import EmailConnectionFactory, RewardsStatus
from automsr.utility import (
    get_config,
    get_safe_credentials,
    show_profiles,
    test_environment,
)

FORMAT = "%(asctime)s :: %(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"
DIVIDER = "-" * 50


def get_logger(verbose: bool, log_format: str = FORMAT):
    formatter = logging.Formatter(log_format)

    stream_level = logging.DEBUG if verbose else logging.INFO
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)

    # file_handler = logging.FileHandler("main.log")
    # file_handler.setLevel(logging.INFO)

    # file_debug_handler = logging.FileHandler("main.debug.log")
    # file_debug_handler.setLevel(logging.DEBUG)

    # set formatters and add handlers to main logger
    logger = logging.getLogger("automsr")
    logger.setLevel(logging.DEBUG)

    handlers = (stream_handler,)

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main(**kwargs):
    # get config filepath from arguments, or defaults to automsr.cfg
    config_fp = kwargs.get("config", "automsr.cfg")
    config = get_config(config_fp)

    # change default config used in module with this one
    automsr.utility.config = config

    # get credentials filepath from config
    credentials_fp = kwargs.get(
        "credentials", automsr.utility.config["automsr"]["credentials"]
    )

    # get logger
    verbose = kwargs.get("verbose", automsr.utility.config["automsr"]["verbose"])
    logger = get_logger(verbose=verbose)

    # test if the flow should only show profiles and then exit
    if kwargs.get("show_profiles"):
        show_profiles()
        return

    # dry run mode, defaults to False
    dry_run = kwargs.get("dry_run", False)

    # parse retry for single account
    retry = automsr.utility.config["automsr"]["retry"]

    # test if env is correctly set
    if not dry_run:
        test_environment(**kwargs)
    # if dry-run, log (debug) current config
    else:
        logger.debug(automsr.utility.config)

    # cycle over credentials, getting points from activities
    all_credentials = list(get_safe_credentials(credentials_fp))
    status_list: List[RewardsStatus] = []

    # check if email creds are valid
    factory = EmailConnectionFactory(all_credentials=all_credentials)
    if factory.send:
        conn = factory.get_connection().test_connection()
        logger.info("A status email will be sent at the end of execution")
        logger.info(f"Sender email: {conn.sender}")
    else:
        logger.warning("No status email will be sent at the end of execution!")

    for credentials in all_credentials:
        logger.info(DIVIDER)

        email = credentials["email"]
        logger.info(f"Working on credentials [email={email}]")
        status = RewardsStatus(email)

        if dry_run:
            logger.info(
                f"Dry run set, so a success status will be recorded for {email}"
            )
            status.set_success("Dry run")
            status_list.append(status)
            continue

        for j in range(retry):
            try:
                success_message = MicrosoftRewards.do_every_activity(
                    credentials=credentials
                )
            except selenium.common.exceptions.InvalidArgumentException as e:
                logger.error(
                    "Error caught with Chromium profiles! "
                    "Maybe you need to close all open windows and retry"
                )
                logger.error(e)
                sys.exit(1)
            except Exception as e:
                msg = f"An error occurred: {e}"
                if not verbose:
                    msg += (
                        "\nTo see its stack enable verbose logging or check debug log."
                    )
                logger.warning(msg)
                logger.debug(e, exc_info=True)
                if j < retry - 1:
                    logger.warning("Retrying...")
                else:
                    logger.error("No more retries!")
                    status.set_failure(str(e))
                    status_list.append(status)
            else:
                logger.info(f"Completed execution for {email}")
                status.set_success(success_message)
                status_list.append(status)
                break

    # at the end of the execution, we'll send the email with the report status
    # with an email connection based on the chosen strategy
    logger.info(DIVIDER)
    logger.info("Execution completed for all credentials")
    if factory.send:
        logger.info("Now sending email...")
        conn = factory.get_connection().open()
        conn.send_status_message(status_list)
        conn.close()
        logger.info("Status email sent correctly to recipient(s)")


if __name__ == "__main__":
    import argparse

    description = (
        "AutoMSR is intended to show how to collect "
        "automatically daily points for Microsoft Rewards."
    )
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-c",
        "--config",
        default="automsr.cfg",
        help="AutoMSR config filepath to use; defaults to automsr.cfg",
    )
    parser.add_argument(
        "-l",
        "--credentials",
        default="credentials.json",
        help="JSON credentials filepath to use; defaults to credentials.json",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Execute AutoMSR in dry-run mode"
    )
    parser.add_argument(
        "--show-profiles",
        action="store_true",
        help="Show Chrome profiles found and then exit",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase console verbosity"
    )

    args = parser.parse_args()
    main(**vars(args))
