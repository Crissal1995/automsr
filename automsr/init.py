import logging
import sys
from pathlib import Path
from typing import Any, List, Optional

import questionary
from attr import asdict, define, field
from prompt_toolkit.shortcuts import CompleteStyle
from questionary import Choice, Style

from automsr.browser.profile import ChromeProfile, ChromeVariant, ProfilesExecutor
from automsr.config import Config, validate_email

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_CONFIG_PATH = Path("config.yaml")

# Styles to use with `questionary` prompts
default_style = Style(
    [
        ("highlighted", "fg:#673ab7 bold"),
        ("qmark", "fg:#673ab7 bold"),
        ("question", "green bold"),
        ("answer", "fg:yellow bold"),
    ]
)

error_style = Style(
    [
        ("question", "red bold"),
        ("answer", "fg:yellow bold"),
    ]
)


def handle_null_response(response: Optional[Any]) -> None:
    """
    Handle null responses provided by the user.

    This is related to how `questionary` handles keyboards interrupts,
    both in a safe or unsafe way.
    We are always using the safe way in the execution flow.

    Docs: https://questionary.readthedocs.io/en/stable/pages/advanced.html#keyboard-interrupts
    """

    # the response will be None if the user cancelled the job, e.g., with CTRL+C
    if response is None:
        sys.exit(1)


def fix_unhandled_exception_in_event_loop() -> None:
    """
    This workaround is needed for an issue with the Python event loop
    and python-prompt-toolkit v3.

    The issue is the following:
        "Exception [WinError 995] The I/O operation has been aborted
        because of either a thread exit or an application request

        Press ENTER to continue..."

    Issue: https://github.com/prompt-toolkit/python-prompt-toolkit/issues/1023
    Workaround: https://github.com/xonsh/xonsh/issues/3430
    """

    def enable_selector_event_loop():
        try:
            # These instructions from
            # https://docs.python.org/3/library/asyncio-eventloop.html?highlight=proactor#asyncio.SelectorEventLoop
            import asyncio
            import selectors

            selector = selectors.SelectSelector()
            loop = asyncio.SelectorEventLoop(selector)
            asyncio.set_event_loop(loop)
        except:  # noqa: E722
            pass

    enable_selector_event_loop()


@define(kw_only=True)
class InitExecutor:
    # Selenium config
    chrome_variant: Optional[ChromeVariant] = None
    profiles_root: Optional[Path] = None
    chromedriver_path: Optional[Path] = None

    # Automsr config
    profiles: Optional[List[ChromeProfile]] = None

    # Email config
    email_enabled: Optional[bool] = None
    email_recipient: Optional[str] = None
    email_sender: Optional[str] = None
    email_sender_password: Optional[str] = field(
        default=None, repr=lambda password: "***"
    )

    # Generic config
    config_path: Optional[Path] = None

    def execute(self) -> None:
        """
        Main functionality to call; will prompt the user how to proceed
        in order to generate a config file automatically.
        """

        # This is needed for python-prompt-toolkit
        fix_unhandled_exception_in_event_loop()

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

        if self.email_enabled is None:
            self.email_enabled = self.get_email_enabled()

        if self.email_enabled:
            if self.email_recipient is None:
                self.email_recipient = self.get_email_recipient()
            if self.email_sender is None:
                self.email_sender = self.get_email_sender()
            if self.email_sender_password is None:
                self.email_sender_password = self.get_email_sender_password()

        config = self.get_config()
        self.store_config(config=config)

    def get_config(self) -> Config:
        """
        Get a config representation based on the status of the object.
        """

        assert self.profiles is not None
        dummy_email = "must-change-this-with-a-correct-email-address@outlook.com"
        profiles_obj = [
            {"email": p.get_email() or dummy_email, "profile": p.path.stem}
            for p in self.profiles
        ]
        if any(profile["email"] == dummy_email for profile in profiles_obj):
            questionary.print(
                text=(
                    "At least one email address was not found automatically. "
                    "Please add it yourself in the config file."
                ),
                style="red bold",
            )
        automsr_obj = {"profiles": profiles_obj}

        assert self.profiles_root is not None
        assert self.chromedriver_path is not None
        selenium_obj = {
            "profiles_root": str(self.profiles_root),
            "chromedriver_path": str(self.chromedriver_path),
        }

        assert self.email_enabled is not None

        if self.email_enabled:
            assert self.email_recipient is not None
            assert self.email_sender is not None
            assert self.email_sender_password is not None
        else:
            logger.debug(
                "Not performing email attributes' check for None, since email sending is disabled."
            )

        email_obj = {
            "enable": self.email_enabled,
            "recipient": self.email_recipient,
            "sender": self.email_sender,
            "sender_password": self.email_sender_password,
        }

        config = Config.from_dict(
            data={
                "automsr": automsr_obj,
                "selenium": selenium_obj,
                "email": email_obj,
            }
        )

        return config

    def store_config(self, config: Config) -> None:
        """
        Store a config object to disk based on the state of this object.
        """

        assert self.config_path is not None
        config.store(path=self.config_path)

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

        chrome_variants: List[str] = [
            variant.name.replace("_", " ").capitalize() for variant in ChromeVariant
        ]

        chrome_variant: Optional[str] = questionary.select(
            message="Which variant of Chrome are you using?",
            choices=chrome_variants,
            use_indicator=True,
            style=default_style,
        ).ask()

        handle_null_response(chrome_variant)
        assert chrome_variant is not None

        variant = list(ChromeVariant)[chrome_variants.index(chrome_variant)]
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

        profiles_executor = self._get_profiles_executor()
        try:
            profiles = profiles_executor.get_profiles()
        except FileNotFoundError as e:
            logger.error(
                "Profiles root directory was not found! "
                "Are you sure that you selected the correct Chrome variant?"
            )
            raise e

        if not profiles:
            logger.error(
                "No Chrome profile found! Create at least one, then try again."
            )
            raise RuntimeError("No Chrome profile found!")

        profiles_as_str = [str(profile) for profile in profiles]
        chosen_profiles: Optional[List[str]] = questionary.checkbox(
            message="Found the following profiles. Select the ones you intend to use.",
            choices=[
                Choice(title=profile, checked=False) for profile in profiles_as_str
            ],
            validate=lambda choices: len(choices) > 0 or "Select at least one profile",
            style=default_style,
        ).ask()

        handle_null_response(chosen_profiles)
        assert chosen_profiles is not None

        profiles_to_use: List[ChromeProfile] = []
        for profile_str in chosen_profiles:
            index: int = profiles_as_str.index(profile_str)
            profile = profiles[index]
            profiles_to_use.append(profile)

        logger.info("Chosen profiles: %s", profiles_to_use)
        return profiles_to_use

    @staticmethod
    def get_chromedriver_path() -> Path:
        """
        Get the Chromedriver path after prompting the user where to find it.
        """

        path_str: Optional[str] = questionary.path(
            "What's the path to the Chromedriver executable?",
            validate=lambda v: Path(v).is_file() or "File not found",
            complete_style=CompleteStyle.READLINE_LIKE,
            style=default_style,
        ).ask()
        handle_null_response(path_str)
        assert path_str is not None
        return Path(path_str)

    @staticmethod
    def get_config_path() -> Path:
        """
        Get the path to the config file.
        """

        while True:
            path_str: Optional[str] = questionary.path(
                "Output path for the YAML Config file. Leave empty for the default: ./config.yaml",
                complete_style=CompleteStyle.READLINE_LIKE,
                validate=lambda v: v == ""
                or not Path(v).is_dir()
                or "Path invalid or directory",
                style=default_style,
            ).ask()
            handle_null_response(path_str)
            assert path_str is not None
            if not path_str:
                path = DEFAULT_CONFIG_PATH
            else:
                path = Path(path_str)
            logger.info("Path provided: %s", path)

            if path.is_file():
                will_overwrite: Optional[bool] = questionary.confirm(
                    message="The path you provided already exists! Do you want to overwrite it?",
                    default=False,
                    style=error_style,
                ).ask()
                handle_null_response(will_overwrite)
                assert will_overwrite is not None
                if will_overwrite:
                    break
            else:
                break

        logger.info("Path that will be used for the config: %s", path)
        return path

    @staticmethod
    def get_email_enabled() -> bool:
        """
        Get a boolean representing if the email sending should be enabled or not.
        """

        email_enabled: Optional[bool] = questionary.confirm(
            message="Do you want to enable the sending of a status email after the execution?",
            default=True,
            style=default_style,
        ).ask()
        handle_null_response(email_enabled)
        assert email_enabled is not None
        return email_enabled

    @staticmethod
    def get_email_recipient() -> str:
        """
        Get the recipient for the status email.
        """

        recipient: Optional[str] = questionary.text(
            message="What is the recipient of the status email?",
            validate=lambda x: True
            if validate_email(x, raise_on_error=False) is not None
            else "Invalid email!",
            style=default_style,
        ).ask()
        handle_null_response(recipient)
        assert recipient is not None
        return recipient

    @staticmethod
    def get_email_sender() -> str:
        """
        Get the sender for the status email.
        """

        sender: Optional[str] = questionary.text(
            message="What is the sender of the status email?",
            validate=lambda x: True
            if validate_email(x, raise_on_error=False) is not None
            else "Invalid email!",
            style=default_style,
        ).ask()
        handle_null_response(sender)
        assert sender is not None
        return sender

    @staticmethod
    def get_email_sender_password() -> str:
        """
        Get the sender's password for the status email.
        """

        password: Optional[str] = questionary.password(
            message=(
                "What is the password of the sender email? "
                "Please use an app password if you activated 2FA on this account."
            ),
            validate=lambda x: bool(x.strip()) or "Empty password!",
            style=default_style,
        ).ask()
        handle_null_response(password)
        assert password is not None
        return password
