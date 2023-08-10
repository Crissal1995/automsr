import logging
from pathlib import Path
from typing import Any

from attr import define
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

from automsr.config import Config, Profile

logger = logging.getLogger(__name__)


class BrowserException(Exception):
    """
    Base class for Browser exceptions.
    """


class CannotChangeUserAgentException(BrowserException):
    """
    Exception raised when the browser is unable to change User Agent.
    """


@define
class BrowserOptions:
    """
    Abstraction of Browser Options, and wrapper around Selenium Chrome Options.
    """

    profiles_root: Path
    profile_directory_name: str

    @classmethod
    def from_config(cls, config: Config, profile: Profile) -> "BrowserOptions":
        """
        Generate the Options based on the profiles_root specified in the `config`, and a chosen `profile`.
        """

        profiles_root = config.selenium.profiles_root
        profile_directory_name = profile.profile

        # safety check
        profile_path = profiles_root / profile_directory_name
        if not profile_path.is_dir():
            raise FileNotFoundError(
                f"Profile `{profile_directory_name}` not found in directory: {profiles_root}"
            )

        return cls(
            profiles_root=profiles_root, profile_directory_name=profile_directory_name
        )

    def as_options(self) -> Options:
        """
        Returns the object as Chromium Options.

        Exhaustive list of Chromium switches: https://peter.sh/experiments/chromium-command-line-switches/
        """

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir={self.profiles_root!s}")
        options.add_argument(f"--profile-directory={self.profile_directory_name}")
        return options


@define
class UserAgent:
    desktop = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"
    )

    mobile = (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.3"
    )


@define
class RewardsUrl:
    bing = "https://www.bing.com/?scope=web"
    rewards = "https://rewards.bing.com/"


@define
class Browser:
    driver: ChromeWebDriver

    user_agents = UserAgent()
    urls = RewardsUrl()

    def change_user_agent(self, user_agent: str, strict: bool = True) -> None:
        """
        Change user agent in the current driver.

        If `check` is True, then the execution will fail if the user agent is not changed.

        Available commands:
        Driver side:
            https://github.com/SeleniumHQ/selenium/blob/selenium-4.11.2-python/py/selenium/webdriver/chromium/remote_connection.py#L36
        Server side:
            https://github.com/SeleniumHQ/selenium/blob/selenium-4.11.2-python/dotnet/src/webdriver/DevTools/Network.cs#L79
        """

        driver_command = "executeCdpCommand"

        server_command = "Network.setUserAgentOverride"
        server_command_args = dict(userAgent=user_agent)

        logger.debug(f"Trying to change user-agent to: {user_agent}")

        self.driver.execute(
            driver_command, {"cmd": server_command, "params": server_command_args}
        )

        actual_user_agent = str(
            self.driver.execute_script("return navigator.userAgent;")
        )
        if actual_user_agent != user_agent:
            if strict:
                raise CannotChangeUserAgentException("Cannot set a new user-agent!")
            else:
                logger.warning(
                    f"Cannot set a new user-agent! Current user-agent: {actual_user_agent}"
                )
        else:
            logger.debug(f"Changed user-agent to: {actual_user_agent}")

    @classmethod
    def from_config(cls, config: Config, profile: Profile) -> "Browser":
        """
        Construct a Browser from a `config` and a `profile` provided as inputs.
        """

        logger.info("Profile to use with Browser: %s", profile)

        if (path := config.selenium.chromedriver_path) is not None:
            chromedriver_path = str(path)
        else:
            chromedriver_path = None
        logger.debug("Chromedriver path: %s", chromedriver_path)

        options = BrowserOptions.from_config(
            config=config, profile=profile
        ).as_options()
        service = Service(chromedriver_path=chromedriver_path)
        driver = ChromeWebDriver(options=options, service=service)
        return cls(driver=driver)

    def test_driver(self) -> None:
        """
        Test if the driver is working correctly.
        """

        test_url = "https://example.org/"
        self.driver.get(test_url)

    def go_to(self, url: str) -> None:
        """
        Change page following the provided url.
        """

        self.driver.get(url)

    def execute_script(self, script: str) -> Any:
        """
        Execute one or more JS instructions and returns the result.
        """

        return self.driver.execute_script(script=script)

    def go_to_bing(self) -> None:
        """
        Change page to Bing homepage.
        """

        return self.go_to(self.urls.bing)

    def go_to_rewards(self) -> None:
        """
        Change page to Rewards homepage.
        """

        return self.go_to(self.urls.rewards)
