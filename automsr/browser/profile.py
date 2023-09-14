import json
import logging
import os
import sqlite3
import sys
from enum import Enum, auto
from pathlib import Path
from typing import ClassVar, Dict, List, Optional, Set, Tuple

from attr import field
from attrs import define

from automsr.config import validate_email

logger = logging.getLogger(__name__)

ENV_HOME = os.environ.get("HOME")
ENV_LOCALAPPDATA = os.environ.get("LOCALAPPDATA")


class ChromeVariant(Enum):
    """
    Chrome variants available
    """

    CHROME = auto()
    CHROME_BETA = auto()
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

    def get_email(self) -> Optional[str]:
        """
        Try to get the Outlook email address from the profile data.
        """

        allowed_domains = {"outlook", "live", "hotmail", "msn"}

        @define(order=True, frozen=True)
        class Record:
            email: str = field(order=False)
            timestamp: int

            @classmethod
            def from_row(cls, row: Tuple[str, str]) -> Optional["Record"]:
                """
                Parse a row obtained from the Login Data database of Chrome.

                If the row is not compatible with our criteria, returns None.
                """

                assert len(row) == 2
                email_value: str = row[0]
                timestamp_value: int = int(row[1])

                if not validate_email(email_value, raise_on_error=False):
                    return None

                domain = email_value.split("@")[1].split(".")[0]
                if domain not in allowed_domains:
                    return None

                return cls(email=email_value, timestamp=timestamp_value)

        # TODO check if this path is valid for every OS
        login_database: Path = self.path / "Login Data"
        if not login_database.is_file():
            logger.debug("No login database found: %s", login_database)
            return None

        with sqlite3.connect(login_database) as conn:
            cur = conn.execute(
                """\
                select t.username_value, t.date_last_used
                from main.logins t
                where t.username_value <> ''
                and t.origin_url like '%live.com%';"""
            )
            all_rows: List[Tuple[str, str]] = cur.fetchall()

        valid_records: List[Optional[Record]] = [
            Record.from_row(row=row) for row in all_rows
        ]
        valid_non_null_records: List[Record] = [
            record for record in valid_records if record is not None
        ]
        unique_emails: Set[str] = {record.email for record in valid_non_null_records}
        logger.debug("Outlook emails found: %s", unique_emails)

        if not unique_emails:
            logger.debug("No Outlook email found!")
            return None
        elif len(unique_emails) > 1:
            logger.debug(
                "More than one Outlook email found! Will return the latest email used."
            )
            latest_record: Record = max(valid_non_null_records)
            return latest_record.email
        else:
            logger.debug("Found only one Outlook email.")
            return unique_emails.pop()


@define
class ProfilesExecutor:
    chrome_variant: ChromeVariant = ChromeVariant.CHROME
    profiles_root_path: Optional[Path] = None

    # source: https://chromium.googlesource.com/chromium/src/+/master/docs/user_data_dir.md#default-location
    CHROME_DEFAULT_PROFILES_LOCATIONS: ClassVar[
        Dict[str, Dict[ChromeVariant, Path]]
    ] = {
        "macOS": {
            ChromeVariant.CHROME: Path(
                f"{ENV_HOME}/Library/Application Support/Google/Chrome"
            ),
            ChromeVariant.CHROME_BETA: Path(
                f"{ENV_HOME}/Library/Application Support/Google/Chrome Beta"
            ),
            ChromeVariant.CHROME_CANARY: Path(
                f"{ENV_HOME}/Library/Application Support/Google/Chrome Canary"
            ),
            ChromeVariant.CHROMIUM: Path(
                f"{ENV_HOME}/Library/Application Support/Chromium"
            ),
        },
        "windows": {
            ChromeVariant.CHROME: Path(
                f"{ENV_LOCALAPPDATA}\\Google\\Chrome\\User Data"
            ),
            ChromeVariant.CHROME_BETA: Path(
                f"{ENV_LOCALAPPDATA}\\Google\\Chrome Beta\\User Data"
            ),
            ChromeVariant.CHROME_CANARY: Path(
                f"{ENV_LOCALAPPDATA}\\Google\\Chrome SxS\\User Data"
            ),
            ChromeVariant.CHROMIUM: Path(f"{ENV_LOCALAPPDATA}\\Chromium\\User Data"),
        },
        "linux": {
            ChromeVariant.CHROME: Path(f"{ENV_HOME}/.config/google-chrome"),
            ChromeVariant.CHROME_BETA: Path(f"{ENV_HOME}/.config/google-chrome-beta"),
            ChromeVariant.CHROME_CANARY: Path(
                f"{ENV_HOME}/.config/google-chrome-unstable"
            ),
            ChromeVariant.CHROMIUM: Path(f"{ENV_HOME}/.config/chromium"),
        },
    }

    def get_profiles_root_path(self) -> Path:
        """
        Based on current state, get the root path of Chrome profiles.
        """

        if self.profiles_root_path is not None:
            logger.info(
                "Profiles root path was manually set to: %s", self.profiles_root_path
            )
            return self.profiles_root_path

        platform = get_platform()
        logger.debug("Platform to use: %s", platform)
        logger.debug("Chrome variant to use: %s", self.chrome_variant)

        profiles_root_path = self.CHROME_DEFAULT_PROFILES_LOCATIONS[platform][
            self.chrome_variant
        ]
        logger.info(
            "Profiles root path was automatically found to be: %s", profiles_root_path
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
