import logging
from argparse import ArgumentParser
from pathlib import Path

from attr import define

from automsr.config import Config
from automsr.executor import SingleTargetExecutor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config.yaml")


@define
class Args:
    """
    CLI Args for the tool
    """

    config: Path = DEFAULT_CONFIG_PATH
    verbose: bool = False


def main(args: Args) -> None:
    # handle verbosity
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)

    config = Config.from_yaml(args.config)
    executor = SingleTargetExecutor(config=config)
    executor.execute()


def cli() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file. Defaults to {DEFAULT_CONFIG_PATH!s}",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    args = Args(**vars(parser.parse_args()))
    main(args=args)


if __name__ == "__main__":
    cli()
