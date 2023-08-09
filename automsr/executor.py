import logging
import time
from typing import Any, Dict, Optional

from attr import define, field
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm

from automsr.browser.browser import Browser
from automsr.config import Config
from automsr.datatypes.dashboard import Dashboard
from automsr.search import RandomSearchGenerator

logger = logging.getLogger(__name__)


@define
class SingleTargetExecutor:
    """
    Executor class driving the completion of all the tasks associated with Rewards.

    In particular, there are several steps to perform to accomplish an execution:
    - Open a new browser session with Selenium and a Chrome driver.
    - Retrieval of dashboard json from Rewards page
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

        # Start a new session
        self.start_session()

        # Retrieve the current
        dashboard = self.get_dashboard()

        # Execute both PC and Mobile searches, if needed
        self.execute_pc_searches(dashboard=dashboard)
        self.execute_mobile_searches(dashboard=dashboard)

    def start_session(self) -> None:
        """
        Create a new session with Selenium and Chromedriver,
        then returns the session object to the caller.
        """

        self.browser = Browser.from_config(config=self.config)
        self.browser.test_driver()
        self.browser.go_to(self.config.automsr.rewards_homepage)

    def get_dashboard(self) -> Dashboard:
        """
        Retrieve a Dashboard object from the current page.

        This method is expected to be run inside the Rewards homepage.
        """

        raw_data: Dict[str, Any] = self.browser.execute_script("return dashboard;")
        dashboard = Dashboard(**raw_data)
        return dashboard

    def execute_pc_searches(self, dashboard: Dashboard) -> None:
        """
        Execute PC searches, if needed.
        """

        if amount := dashboard.amount_of_pc_searches() == 0:
            logger.info("No PC search is needed.")
            return

        logger.info("Executing %s PC searches.", amount)
        return self._execute_searches(
            amount=amount, user_agent=self.browser.user_agents.desktop
        )

    def execute_mobile_searches(self, dashboard: Dashboard) -> None:
        """
        Execute Mobile searches, if needed.
        """

        if amount := dashboard.amount_of_mobile_searches() == 0:
            logger.info("No Mobile search is needed.")
            return

        logger.info("Executing %s Mobile searches.", amount)
        return self._execute_searches(
            amount=amount, user_agent=self.browser.user_agents.mobile
        )

    def _execute_searches(
        self, amount: int = 1, user_agent: Optional[str] = None
    ) -> None:
        """
        Helper method to execute `amount` searches.

        Can specify a custom `user_agent` to use.
        """

        assert amount >= 1, "Invalid value!"

        safe_amount = amount + 5
        logger.info("Original amount of searches: %s", amount)
        logger.info("Safe amount of searches: %s", safe_amount)

        if user_agent is not None:
            logger.info("Changing user-agent to: %s", user_agent)
            self.browser.change_user_agent(user_agent=user_agent)

        search_generator = RandomSearchGenerator()
        sleep_time = search_generator.sleep_time()
        query = search_generator.query_gen()

        self.browser.go_to_bing()

        for i in tqdm(range(amount)):
            logger.debug("Executing search: %s/%s", i + 1, amount)

            # we retrieve the element in the for-loop since the page is reloaded, thus the element can be invalidated
            element: WebElement = self.browser.driver.find_element(
                by=By.ID, value="sb_form_q"
            )

            # send the next item of the generator to the input field
            element.send_keys(next(query))

            # sleep to prevent issues with Selenium interacting with the page
            time.sleep(0.5)

            # send ENTER to perform a search
            element.send_keys(Keys.ENTER)

            # sleep a certain amount of time
            time.sleep(sleep_time)

        logger.debug("Finished searches")
