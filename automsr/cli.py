import logging
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Callable

from attr import define, field

from automsr.browser.profile import OutputFormat, ProfilesExecutor
from automsr.config import Config
from automsr.executor import MultipleTargetsExecutor
from automsr.mail import EmailExecutor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config.yaml")


@define
class Args:
    """
    Class mapping of CLI arguments.
    """

    # Method to invoke with a specific subparser
    func: Callable[["Args"], Any]

    # Common args
    config: Path = DEFAULT_CONFIG_PATH
    verbose: bool = False

    # Run args

    # Profiles args
    format: OutputFormat = field(default=OutputFormat.LIST, converter=OutputFormat)


def run(args: Args) -> None:
    """
    Method to invoke when `run` is executed.
    """

    config = Config.from_yaml(args.config)
    executor = MultipleTargetsExecutor(config=config)
    executor.execute()
    logger.info("Execution finished!")


def profiles(args: Args) -> None:
    """
    Method to invoke when `profiles` is executed.
    """

    config = Config.from_yaml(args.config)
    executor = ProfilesExecutor(profiles_root_path=config.selenium.profiles_root)
    executor.print_profiles(output_format=args.format)


def email(args: Args) -> None:
    """
    Method to invoke when `email` is executed.
    """

    config = Config.from_yaml(args.config)
    executor = EmailExecutor(config=config)
    if executor.are_messages_enabled():
        executor.send_mock_message()
    else:
        logger.error(
            "Cannot test emails if messages are not enabled!"
            " Check your config file and retry."
        )
        sys.exit(1)


def add_common_flags(parser: ArgumentParser) -> None:
    """
    Add common flags to a generic parser.

    Flags provided:
    * -c, --config
    * -v, --verbose
    """

    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file. Defaults to {DEFAULT_CONFIG_PATH!s}",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )


def add_run_flags(parser: ArgumentParser) -> None:
    """
    Add `run` flags to a generic parser.

    Flags provided: no one.
    """

    parser.set_defaults(func=run)


def add_profiles_flags(parser: ArgumentParser) -> None:
    """
    Add `profiles` flags to a generic parser.

    Flags provided:
    * -f, --format
    """

    parser.add_argument(
        "-f",
        "--format",
        default=OutputFormat.LIST.value,
        choices=[v.value for v in list(OutputFormat)],
        help=f"Output format for profiles. Defaults to {OutputFormat.LIST.value}",
    )
    parser.set_defaults(func=profiles)


def add_email_flags(parser: ArgumentParser) -> None:
    """
    Add `email` flags to a generic parser.

    Flags provided: no one.
    """

    parser.set_defaults(func=email)


def cli() -> None:
    # Construct the base parser
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(required=True, help="Available subcommands.")

    # Construct the `run` parser
    run_parser = subparsers.add_parser(
        name="run",
        help="Run AutoMSR on profiles specified in the config file, then exit.",
    )
    add_common_flags(parser=run_parser)
    add_run_flags(parser=run_parser)

    # Construct the `profiles` parser
    profiles_parser = subparsers.add_parser(
        name="profiles",
        help="Retrieve the Chrome profiles found in the local machine with their full path.",
    )
    add_common_flags(parser=profiles_parser)
    add_profiles_flags(parser=profiles_parser)

    # Construct the `email` parser
    email_parser = subparsers.add_parser(
        name="email",
        help="Send a test email to the recipient specified in the config file.",
    )
    add_common_flags(parser=email_parser)
    add_email_flags(parser=email_parser)

    # Parse arguments
    try:
        raw_args = vars(parser.parse_args())
    except TypeError:
        parser.print_help()
        sys.exit(1)
    args = Args(**raw_args)

    # Handle verbosity
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    # Set external libraries' logging level to WARNING.
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("faker").setLevel(logging.WARNING)
    logging.getLogger("MARKDOWN").setLevel(logging.WARNING)

    # Execute subparser functionality
    args.func(args)


if __name__ == "__main__":
    cli()
