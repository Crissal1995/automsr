from attr import define, field

from automsr.browser.browser import Browser
from automsr.config import Config


@define
class SingleTargetExecutor:
    """
    Executor class driving the completion of all the tasks associated with Rewards.

    In particular, there are several steps to perform to accomplish an execution:
    - Open a new browser session with Selenium and a Chrome driver.
    - Retrieval of status json from Rewards page
    - TODO Execution of all completable punchcards
    - Execution of all completable promotions
    - Execution of searches:
        - PC searches (desktop user agent)
        - Mobile searches (mobile user agent)

    This executor will target a single profile.
    """

    config: Config
    browser: Browser = field(init=False)

    def execute(self) -> None:
        """
        Execute the steps mentioned in the class doctest.
        """

    def start_session(self) -> None:
        """
        Create a new session with Selenium and Chromedriver,
        then returns the session object to the caller.
        """

        self.browser = Browser.from_config(config=self.config)
        self.browser.test_driver()
        self.browser.go_to(self.config.automsr.rewards_homepage)
