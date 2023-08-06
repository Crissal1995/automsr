import json
import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List

from attrs import define

logger = logging.getLogger(__name__)

ENV_HOME = os.environ.get("HOME")
ENV_LOCALAPPDATA = os.environ.get("LOCALAPPDATA")

CHROME_PROFILES_LOCATIONS: Dict[str, List[str]] = {
    "macOS": [
        f"{ENV_HOME}/Library/Application Support/Google/Chrome",
        f"{ENV_HOME}/Library/Application Support/Google/Chrome Canary",
        f"{ENV_HOME}/Library/Application Support/Chromium",
    ],
    "windows": [
        f"{ENV_LOCALAPPDATA}\\Google\\Chrome\\User Data",
        f"{ENV_LOCALAPPDATA}\\Google\\Chrome SxS\\User Data",
        f"{ENV_LOCALAPPDATA}\\Chromium\\User Data",
    ],
    "linux": [
        f"{ENV_HOME}/.config/google-chrome",
        f"{ENV_HOME}/.config/google-chrome-beta",
        f"{ENV_HOME}/.config/chromium",
    ],
}


class ChromeVariant(Enum):
    """
    Chrome variants available
    """

    CHROME = 0
    CHROME_CANARY = 1
    CHROMIUM = 2


@define
class ChromeProfile:
    name: str
    path: Path

    def as_dict(self) -> Dict[str, str]:
        return dict(name=self.name, path=str(self.path.resolve()))


def get_chrome_profile_location(variant: ChromeVariant) -> Path:
    """
    Returns Chrome profiles' path associated with current platform and selected variant
    """

    key = "linux"  # assumes linux env if not win32 or darwin

    if sys.platform.startswith("win32"):
        key = "windows"
    elif sys.platform.startswith("darwin"):
        key = "macOS"

    return Path(CHROME_PROFILES_LOCATIONS[key][variant.value])


def get_all_chrome_profile_locations() -> Dict[ChromeVariant, Path]:
    """
    Returns a list of all available Chrome profiles' locations, trying every ChromeVariant.
    """

    paths = {}

    for name, value in ChromeVariant.__members__.items():
        path = get_chrome_profile_location(variant=value)
        if path.exists():
            logger.info(f"Chrome variant found: {name}")
            logger.debug(f"Chrome variant profiles path: {path}")
            paths[value] = path

    if not paths:
        err = "No default location path for Chrome profiles was found!"
        raise FileNotFoundError(err)
    else:
        return paths


def parse_profiles(userdata_path: Path) -> List[ChromeProfile]:
    """
    Get a list of Chrome profiles, starting from the root user data path.
    """

    profiles = []

    for dir_ in userdata_path.iterdir():
        # if it's not a folder, surely it's not a profile
        if not dir_.is_dir():
            continue

        # if current profile is one of the blacklisted profiles, continue
        blacklisted_profiles = ("System Profile", "Guest Profile")
        if dir_.stem in blacklisted_profiles:
            continue

        # if this file doesn't exist, it's not a profile
        preferences_path = dir_ / "Preferences"
        if not preferences_path.is_file():
            continue

        preferences_dict = json.load(open(preferences_path, encoding="utf-8"))
        name = preferences_dict.get("profile", {}).get("name", "")
        profile = ChromeProfile(
            name=name,
            path=dir_,
        )
        profiles.append(profile)

    return profiles


def print_profiles() -> None:
    """
    Retrieve Chrome profiles for all Chrome variants found and print them to stdout.
    """

    all_paths = get_all_chrome_profile_locations()
    all_profiles_as_dict = []
    for variant, rootpath in all_paths.items():
        profiles = parse_profiles(userdata_path=rootpath)

        logger.info("Found %s Chrome profiles for variant %s", len(profiles), variant)
        all_profiles_as_dict.extend([profile.as_dict() for profile in profiles])

    print(json.dumps(all_profiles_as_dict))
