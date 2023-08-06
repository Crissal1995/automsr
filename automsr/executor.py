from attr import define, field
from selenium.webdriver.remote.webdriver import WebDriver


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

    driver: WebDriver = field(init=False)

    def execute(self) -> None:
        """
        Execute the steps mentioned in the class doctest.
        """

    def start_session(self) -> None:
        """
        Create a new session with Selenium and Chromedriver,
        then returns the session object to the caller.
        """
