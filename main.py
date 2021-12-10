import logging

import selenium.common.exceptions

import msrewards.utility
from msrewards import MicrosoftRewards
from msrewards.mail import OutlookEmailConnection, RewardsStatus
from msrewards.utility import get_config, get_safe_credentials, test_environment


def get_logger(verbose: bool):
    FORMAT = "%(asctime)s :: %(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"
    formatter = logging.Formatter(FORMAT)

    stream_level = logging.DEBUG if verbose else logging.INFO
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)

    file_handler = logging.FileHandler("main.log")
    file_handler.setLevel(logging.INFO)

    file_debug_handler = logging.FileHandler("main.debug.log")
    file_debug_handler.setLevel(logging.DEBUG)

    # set formatters and add handlers to main logger
    logger = logging.getLogger("msrewards")
    logger.setLevel(logging.DEBUG)

    handlers = (stream_handler, file_handler, file_debug_handler)

    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main(**kwargs):
    # get config filepath from arguments, or defaults to automsr.cfg
    config_fp = kwargs.get("config", "automsr.cfg")
    config = get_config(config_fp)

    # change default config used in module with this one
    msrewards.utility.config = config

    # get credentials filepath from config
    credentials_fp = kwargs.get("credentials", config["automsr"]["credentials"])

    # get logger
    verbose = kwargs.get("verbose", config["automsr"]["verbose"])
    logger = get_logger(verbose=verbose)

    # dry run mode, defaults to False
    dry_run = kwargs.get("dry_run", False)

    # hardcoded because it should be 2 at least
    retry = 5

    # test if env is correctly set
    if not dry_run:
        test_environment(**kwargs)

    # if the email is not null or empty string, it will be used
    send_email = bool(config["automsr"]["email"])
    if send_email:
        logger.info(
            "Recipient email found, so emails will be"
            " sent in case of success/failure"
        )
    else:
        logger.info(
            "No recipient email was found, so no email will be"
            " sent in case of success/failure"
        )

    credentials_sender = None
    status_list: [RewardsStatus] = []

    # cycle over credentials, getting points from activities
    for i, credentials in enumerate(get_safe_credentials(credentials_fp)):
        # take the first credentials set as only one sender
        if i == 0:
            credentials_sender = credentials

        # if we're iterating over multiple credentials, print a divider
        if i > 0:
            logger.info("-" * 30)

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
                raise e from None
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

    # at the end of the cycle, we'll send the email with the report status
    # if credentials_sender is set (there is almost one credentials to work with)
    # and if recipient is set
    if send_email and credentials_sender:
        with OutlookEmailConnection(credentials_sender) as conn:
            conn.send_status_message(status_list)
        logger.info("Email sent to receipt correctly")


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
        "-v", "--verbose", action="store_true", help="Increase console verbosity"
    )

    args = parser.parse_args()
    main(
        config=args.config,
        credentials=args.credentials,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
