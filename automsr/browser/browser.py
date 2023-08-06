import logging

from attr import define
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver

from automsr.config import Config

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
    @classmethod
    def from_config(cls, config: Config) -> "BrowserOptions":
        raise NotImplementedError

    def as_options(self) -> Options:
        raise NotImplementedError


@define
class Browser:
    driver: ChromeWebDriver

    def change_user_agent(self, user_agent: str, check: bool = True) -> None:
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

        self.driver.execute(
            driver_command, {"cmd": server_command, "params": server_command_args}
        )

        actual_user_agent = str(
            self.driver.execute_script("return navigator.userAgent;")
        )
        if check and actual_user_agent != user_agent:
            raise CannotChangeUserAgentException("Cannot set a new user-agent!")
        else:
            logger.debug(f"Changed user-agent to: {user_agent}")

    @classmethod
    def from_config(cls, config: Config) -> "Browser":
        """
        Construct a Browser from a Chrome executable path provided as input.
        """

        options = BrowserOptions.from_config(config=config).as_options()
        service = Service()
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
