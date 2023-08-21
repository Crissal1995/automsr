import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Callable

from attr import define

from automsr.config import Config
from automsr.executor import MultipleTargetsExecutor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config.yaml")


@define
class Args:
    func: Callable[..., Any]
    config: Path = DEFAULT_CONFIG_PATH
    verbose: bool = False


def add_common_flags(parser: ArgumentParser) -> None:
    """
    Add common flags to a generic parser.

    They include:
    * --verbose
    """

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )


def main(args: Args) -> None:
    config = Config.from_yaml(args.config)
    executor = MultipleTargetsExecutor(config=config)
    executor.execute()


def cli() -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(
        required=True, title="subcommands", description="valid subcommands"
    )

    # Construct `run` parser
    run_parser = subparsers.add_parser(name="run")
    run_parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file. Defaults to {DEFAULT_CONFIG_PATH!s}",
    )
    add_common_flags(parser=run_parser)

    # Construct `profiles` parser
    profiles_parser = subparsers.add_parser(name="profiles")
    add_common_flags(parser=profiles_parser)

    raw_args = vars(parser.parse_args())
    args = Args(**raw_args)

    # handle verbosity
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    # execute main functionality
    main(args=args)


if __name__ == "__main__":
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    cli()
