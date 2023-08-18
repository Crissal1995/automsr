import logging
from argparse import ArgumentParser
from pathlib import Path

from attr import define

from automsr.config import Config
from automsr.executor import MultipleTargetsExecutor

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("config.yaml")


@define
class Args:
    config: Path = DEFAULT_CONFIG_PATH
    verbose: bool = False


def main(args: Args) -> None:
    config = Config.from_yaml(args.config)
    executor = MultipleTargetsExecutor(config=config)
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
