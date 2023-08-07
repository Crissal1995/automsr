import logging
from typing import Any, Dict, Optional

from attr import define, field

from automsr.browser.browser import Browser
from automsr.config import Config
from automsr.datatypes.dashboard import Dashboard

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

        if not dashboard.can_search_on_pc():
            logger.info("No PC search is needed.")
            return

        logger.info("Executing PC searches.")
        self._execute_searches(user_agent=self.browser.desktop_user_agent)

    def execute_mobile_searches(self, dashboard: Dashboard) -> None:
        """
        Execute Mobile searches, if needed.
        """

        if not dashboard.can_search_on_mobile():
            logger.info("No Mobile search is needed.")
            return

        logger.info("Executing Mobile searches.")
        return self._execute_searches(user_agent=self.browser.mobile_user_agent)

    def _execute_searches(self, user_agent: Optional[str] = None) -> None:
        """
        Helper method to execute searches.
        """

        if user_agent is not None:
            self.browser.change_user_agent(user_agent=user_agent)

        raise NotImplementedError
