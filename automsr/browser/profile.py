import json
import logging
import os
import sys
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional

from attrs import define

logger = logging.getLogger(__name__)

ENV_HOME = os.environ.get("HOME")
ENV_LOCALAPPDATA = os.environ.get("LOCALAPPDATA")


class ChromeVariant(Enum):
    """
    Chrome variants available
    """

    CHROME = auto()
    CHROME_CANARY = auto()
    CHROMIUM = auto()


class OutputFormat(Enum):
    """
    Types of output formats available for printing found Chrome profiles o stdout.
    """

    LIST = "list"
    JSON = "json"
    PRETTY_JSON = "pretty-json"


def get_platform() -> str:
    """
    Returns a simplified version of the system platform in use.
    """

    retval = "linux"  # assumes linux env if not win32 or darwin

    if sys.platform.startswith("win32"):
        retval = "windows"
    elif sys.platform.startswith("darwin"):
        retval = "macOS"

    return retval


@define
class ChromeProfile:
    displayed_name: str
    path: Path

    RESERVED_NAMES = ["System Profile", "Guest Profile"]

    def as_dict(self) -> Dict[str, str]:
        return dict(displayed_name=self.displayed_name, path=str(self.path.resolve()))

    @classmethod
    def from_directory(cls, path: Path) -> Optional["ChromeProfile"]:
        """
        Returns a Chrome Profile based on a directory.

        Returns `None` if the provided `path` is not a valid Chrome Profile.
        """

        # If the provided path is not an existing directory, returns None
        if not path.is_dir():
            return None

        # If the directory name is one of the reserved name for Google profiles
        # not matching any user profile, returns None
        if path.name in cls.RESERVED_NAMES:
            return None

        # If this file doesn't exist, it's not a profile
        preferences_path = path / "Preferences"
        if not preferences_path.is_file():
            return None

        preferences_dict = json.load(open(preferences_path, encoding="utf-8"))
        displayed_name = preferences_dict.get("profile", {}).get("name", "")
        return cls(displayed_name=displayed_name, path=path)


@define
class ProfilesExecutor:
    chrome_variant: ChromeVariant = ChromeVariant.CHROME
    profiles_root_path: Optional[Path] = None

    CHROME_PROFILES_LOCATIONS = {
        "macOS": {
            ChromeVariant.CHROME: f"{ENV_HOME}/Library/Application Support/Google/Chrome",
            ChromeVariant.CHROME_CANARY: f"{ENV_HOME}/Library/Application Support/Google/Chrome",
            ChromeVariant.CHROMIUM: f"{ENV_HOME}/Library/Application Support/Google/Chrome",
        },
        "windows": {
            ChromeVariant.CHROME: f"{ENV_LOCALAPPDATA}\\Google\\Chrome\\User Data",
            ChromeVariant.CHROME_CANARY: f"{ENV_LOCALAPPDATA}\\Google\\Chrome SxS\\User Data",
            ChromeVariant.CHROMIUM: f"{ENV_HOME}/Library/Application Support/Chromium",
        },
        "linux": {
            ChromeVariant.CHROME: f"{ENV_HOME}/.config/google-chrome",
            ChromeVariant.CHROME_CANARY: f"{ENV_HOME}/.config/google-chrome-beta",
            ChromeVariant.CHROMIUM: f"{ENV_HOME}/.config/chromium",
        },
    }

    def get_profiles_root_path(self) -> Path:
        """
        Based on current state, get the root path of Chrome profiles.
        """

        if self.profiles_root_path is not None:
            logger.info(
                "Profiles root path manually set to: %s", self.profiles_root_path
            )
            return self.profiles_root_path

        platform = get_platform()
        logger.debug("Platform to use: %s", platform)
        logger.debug("Chrome variant to use: %s", self.chrome_variant)

        profiles_root_path_str = self.CHROME_PROFILES_LOCATIONS[platform][
            self.chrome_variant
        ]
        profiles_root_path = Path(profiles_root_path_str)
        logger.info(
            "Profiles root path automatically found to be: %s", profiles_root_path
        )
        return profiles_root_path

    def get_profiles(self) -> List[ChromeProfile]:
        """
        Return the list of Chrome profiles found.
        """

        root_path = self.get_profiles_root_path()

        # Safety check
        if not root_path.exists():
            raise FileNotFoundError(root_path)

        chrome_profiles: List[ChromeProfile] = []

        for directory in root_path.iterdir():
            chrome_profile = ChromeProfile.from_directory(path=directory)
            if chrome_profile is None:
                continue

            logger.info("Found Chrome profile: %s", chrome_profile)
            chrome_profiles.append(chrome_profile)

        return chrome_profiles

    def print_profiles(self, output_format: OutputFormat = OutputFormat.LIST) -> None:
        """
        Get the list of Chrome profiles found, then print it to stdout.

        It's possible to specify a type for printing the values obtained to stdout.
        """

        profiles: List[ChromeProfile] = self.get_profiles()

        if output_format is OutputFormat.LIST:
            data = "\n".join([str(profile) for profile in profiles])

        elif output_format is OutputFormat.JSON:
            data = json.dumps([profile.as_dict() for profile in profiles])

        elif output_format is OutputFormat.PRETTY_JSON:
            data = json.dumps([profile.as_dict() for profile in profiles], indent=4)

        else:
            raise ValueError(output_format)

        data += "\n"  # add manually a final newline
        sys.stdout.write(data)
