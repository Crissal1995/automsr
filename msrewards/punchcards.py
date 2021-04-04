import enum
import logging
import time
from abc import ABC

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class PunchcardStatus(enum.IntEnum):
    TODO = 0
    DONE = 1
    INVALID = 2


class Punchcard(ABC):
    start_selector = "section > div > div > div > a"

    def __init__(self, driver: WebDriver, element: WebElement):
        self.driver = driver
        self.element = element
        self.text = element.get_attribute("aria-label")
        checkmarks = element.find_elements_by_class_name("mee-icon")
        if not checkmarks:
            logging.warning(
                f"No checkmarks found for punchcard. Is it valid? (text={self.text})."
            )
            status = PunchcardStatus.INVALID
        else:
            if all(
                "checkmark" in checkmark.get_attribute("class")
                for checkmark in checkmarks
            ):
                status = PunchcardStatus.DONE
            else:
                status = PunchcardStatus.TODO
        logging.debug(f"Punchcard status is {status}")
        self.status = status
        self.button = element.find_element_by_css_selector(self.start_selector)

    def do_it(self):
        raise NotImplementedError

    def __repr__(self):
        return f"Punchcard(status={self.status}, text={self.text})"


class PaidPunchcard(Punchcard, ABC):
    keywords = (
        "compra",
        "comprare",
        "noleggia",
        "noleggiare",
        "acquista",
        "acquistare",
        "spendi",
        "spendere",
    )

    def __repr__(self):
        return f"Paid{super().__repr__()}"


class FreePunchcard(Punchcard):
    def __repr__(self):
        return f"Free{super().__repr__()}"

    @staticmethod
    def is_complete(punchcard_element: WebElement):
        span = punchcard_element.find_element_by_tag_name("span")
        spanclass = span.get_attribute("class")
        return "punchcard-complete" in spanclass

    def do_it(self):
        row_class = "punchcard-row"
        punchcards = self.driver.find_elements_by_class_name(row_class)
        logging.debug(f"Found {len(punchcards)} punchcards actions inside {str(self)}")
        todo_punchcards = [
            punchcard for punchcard in punchcards if not self.is_complete(punchcard)
        ]
        logging.debug(
            f"Found {len(todo_punchcards)} todo punchcards actions inside {str(self)}"
        )
        home_win = self.driver.current_window_handle
        for i, punchcard in enumerate(todo_punchcards):
            punchcard.find_element_by_tag_name("a").click()
            logging.debug(f"Punchcard action no. {i + 1} completed")
            time.sleep(2)
            self.driver.switch_to.window(home_win)
