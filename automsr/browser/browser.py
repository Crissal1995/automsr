import logging
from pathlib import Path
from typing import Any, Optional

from attr import define
from selenium.common import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By

from automsr.config import Config, Defaults, Profile
from automsr.datatypes.dashboard import Promotion

logger = logging.getLogger(__name__)


class BrowserException(Exception):
    """
    Base class for Browser exceptions.
    """


class CannotChangeUserAgentException(BrowserException):
    """
    Exception raised when the browser is unable to change User Agent.
    """


class CannotStartBrowserException(BrowserException):
    """
    Exception raised when Selenium is unable to start a new Browser Session.
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

    def as_chromium(self) -> Options:
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
    desktop: str = Defaults.desktop_useragent
    mobile: str = Defaults.mobile_useragent


@define
class RewardsUrl:
    bing: str = Defaults.bing_homepage
    rewards: str = Defaults.rewards_homepage


@define
class Browser:
    driver: ChromeWebDriver

    user_agents: UserAgent = UserAgent()
    urls: RewardsUrl = RewardsUrl()

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

        actual_user_agent = self.get_user_agent()
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

        if (path := config.selenium.chromedriver_path) is not None:
            chromedriver_path = str(path)
        else:
            chromedriver_path = None
        logger.debug("Chromedriver path: %s", chromedriver_path)

        user_agents = UserAgent(
            desktop=config.automsr.desktop_useragent,
            mobile=config.automsr.mobile_useragent,
        )
        urls = RewardsUrl(
            bing=config.automsr.bing_homepage,
            rewards=config.automsr.rewards_homepage,
        )

        logger.debug("User agents used: %s", user_agents)
        logger.debug("Rewards URLs used: %s", urls)

        options = BrowserOptions.from_config(config=config, profile=profile)
        logger.debug("Browser options: %s", options)

        chromium_options = options.as_chromium()
        service = Service(chromedriver_path=chromedriver_path)
        try:
            driver = ChromeWebDriver(options=chromium_options, service=service)
            driver.implicitly_wait(time_to_wait=3)
        except WebDriverException as e:
            exception = CannotStartBrowserException(
                "Cannot create a new Chrome Session! Maybe there is already one process running?"
            )
            raise exception from e

        return cls(driver=driver, user_agents=user_agents, urls=urls)

    def test_driver(self) -> None:
        """
        Test if the driver is working correctly.
        """

        test_url = "https://www.google.com"
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

    def get_user_agent(self) -> str:
        """
        Returns the current User-Agent.
        """

        return str(self.driver.execute_script("return navigator.userAgent;"))

    def change_window(self, handle_name: str) -> None:
        """
        Switch window to the one specified by the handle name.
        """

        windows = self.driver.window_handles
        window_index = windows.index(handle_name)
        window = windows[window_index]
        self.driver.switch_to.window(window)

    def open_promotion(
        self, promotion: Promotion, element_id: Optional[str] = None
    ) -> None:
        """
        Open correctly a Promotion found in the Rewards homepage.

        If the `element-id` is provided, use that to retrieve the WebElement from the page.
        """

        current_url: str = self.driver.current_url
        rewards_url: str = self.urls.rewards

        if not current_url.startswith(rewards_url):
            logger.debug("Changing current page to Rewards homepage.")
            self.go_to_rewards()

        if element_id is not None:
            logger.debug("Searching for promotion with id: %s", element_id)
            if not element_id:
                raise ValueError("Empty element id!")
            promotion_element = self.driver.find_element(by=By.ID, value=element_id)
        else:
            css_selector_value = (
                f'.rewards-card-container[data-bi-id="{promotion.name}"]'
            )
            logger.debug(
                "Searching for promotion with css selector: %s", css_selector_value
            )
            promotion_element = self.driver.find_element(
                by=By.CSS_SELECTOR, value=css_selector_value
            )

        logger.debug("Promotion found! Clicking it to trigger the promotion start.")

        # store window handles before the click
        handles_before = self.driver.window_handles

        # click the element
        promotion_element.click()

        # store window handles after the click
        handles_after = self.driver.window_handles

        handle = set(handles_after).difference(handles_before).pop()
        self.change_window(handle_name=handle)
