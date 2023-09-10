import logging
import sys
from pathlib import Path
from typing import List, Optional

from attr import asdict, define
from beaupy import confirm, prompt, select, select_multiple
from rich.console import Console

from automsr.browser.profile import ChromeProfile, ChromeVariant, ProfilesExecutor

DEFAULT_CONFIG_PATH = Path("config.yaml")

logger = logging.getLogger(__name__)


@define(kw_only=True)
class InitExecutor:
    # Selenium config
    chrome_variant: Optional[ChromeVariant] = None
    profiles_root: Optional[Path] = None
    chromedriver_path: Optional[Path] = None

    # Automsr config
    profiles: Optional[List[ChromeProfile]] = None

    # Generic config
    config_path: Optional[Path] = None

    def execute(self) -> None:
        """
        Main functionality to call; will prompt the user how to proceed
        in order to generate a config file automatically.
        """

        self.check_if_interactive_shell_is_needed()

        if self.chrome_variant is None:
            self.chrome_variant = self.get_chrome_variant()

        if self.profiles_root is None:
            self.profiles_root = self.get_chrome_profiles_root()

        if self.profiles is None:
            self.profiles = self.get_chrome_profiles()

        if self.chromedriver_path is None:
            self.chromedriver_path = self.get_chromedriver_path()

        if self.config_path is None:
            self.config_path = self.get_config_path()

    def check_if_interactive_shell_is_needed(self) -> None:
        """
        Check if an interactive shell is needed, based on the state of the object.

        Raise if is needed and the current shell is not interactive.
        """

        members = asdict(self)

        acceptable_null_members = {"profiles_root"}
        for member in acceptable_null_members:
            members.pop(member)

        if any(value is None for value in members.values()):
            self.assert_interactive_shell()

    @staticmethod
    def assert_interactive_shell() -> None:
        """
        Check if the current shell is interactive.

        Raise a `RuntimeError` if this is not True.
        """

        if not sys.stdout.isatty():
            logger.error("Current shell is not interactive!")
            logger.warning(
                "To enable this command to be executed, please provide non-null values for every class member."
            )
            raise RuntimeError("Current shell is not interactive!")
        else:
            logger.debug("Current shell is interactive.")

    @staticmethod
    def get_chrome_variant() -> ChromeVariant:
        """
        Get the Chrome variant after asking the user to select it from a list.
        """

        console = Console()
        console.print(
            "Which variant of Chrome are you using? Select [b u]Chrome[/] if you are unsure."
        )
        chrome_variants = [
            variant.name.replace("_", " ").capitalize().replace("_", "")
            for variant in ChromeVariant
        ]
        variant_index: int = select(options=chrome_variants, return_index=True)
        variant = list(ChromeVariant)[variant_index]
        logger.info("Variant selected: %s", variant)
        return variant

    def _get_profiles_executor(self) -> ProfilesExecutor:
        """
        Get a Profiles Executor based on the status of the object.
        """

        if self.chrome_variant is not None:
            return ProfilesExecutor(
                chrome_variant=self.chrome_variant,
                profiles_root_path=self.profiles_root,
            )
        else:
            return ProfilesExecutor(profiles_root_path=self.profiles_root)

    def get_chrome_profiles_root(self) -> Path:
        """
        Get the current Chrome profiles root.
        """

        profiles_executor = self._get_profiles_executor()
        return profiles_executor.get_profiles_root_path()

    def get_chrome_profiles(self) -> List[ChromeProfile]:
        """
        Set the Chrome profiles based on the selected Chrome variant and the user prompt.
        """

        console = Console()

        profiles_executor = self._get_profiles_executor()
        profiles = profiles_executor.get_profiles()

        if not profiles:
            logger.error(
                "No Chrome profile found! Create at least one, then try again."
            )
            raise RuntimeError("No Chrome profile found!")

        profiles_str = [str(profile) for profile in profiles]
        console.print("Found the following profiles. De-select them at will.")
        indices: List[int] = select_multiple(
            options=profiles_str,
            return_indices=True,
            ticked_indices=list(range(len(profiles_str))),
            minimal_count=1,
        )

        profiles_to_use: List[ChromeProfile] = []
        for index in indices:
            profiles_to_use.append(profiles[index])

        return profiles_to_use

    @staticmethod
    def get_chromedriver_path() -> Path:
        """
        Get the Chromedriver path after prompting the user where to find it.
        """

        console = Console()
        console.print("Specify the path to the Chromedriver executable.")
        console.print(
            "Leave empty for the default, [b u]chromedriver[/]. "
            "It will be looked for in the PATH env variable."
        )

        str_path = prompt("Path:")
        if not str_path:
            path = Path("chromedriver")
        else:
            path = Path(str_path)
            if not path.is_file():
                raise FileNotFoundError(path)

        return path

    @staticmethod
    def get_config_path() -> Path:
        """
        Get the path to the config file.
        """

        console = Console()

        while True:
            str_path = prompt(
                "Path to output the Config file. Leave empty for the default, [b u]config.yaml[/]"
            )
            path = Path(str_path)
            if not path.is_file():
                break
            else:
                console.print("[b red]The path you provided already exists.[/]")
                should_overwrite = confirm("Do you want to overwrite it?")
                if should_overwrite:
                    break

        return path
