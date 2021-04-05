import enum
import logging
import time
from abc import ABC

from selenium.common import exceptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class Status(enum.IntEnum):
    TODO = 0
    DONE = 1
    INVALID = 2


class Runnable(ABC):
    @property
    def button(self):
        raise NotImplementedError

    def do_it(self):
        raise NotImplementedError


class Activity(Runnable, ABC):
    base_header = None

    status_selector = "mee-rewards-points > div > div > span.mee-icon"
    header_selector = "div.contentContainer > h3"
    text_selector = "div.contentContainer > p"
    button_selector = "div.actionLink > a > span"

    def __init__(self, driver: WebDriver, element: WebElement):
        self.driver = driver
        self.element = element

        try:
            status_class = element.find_element_by_css_selector(
                self.status_selector
            ).get_attribute("class")
            self.status = Activity.get_status(status_class)
        except exceptions.NoSuchElementException:
            self.status = Status.INVALID

        self.header = element.find_element_by_css_selector(self.header_selector).text
        self.text = element.find_element_by_css_selector(self.text_selector).text
        self._button = element.find_elements_by_css_selector(self.button_selector)[-1]

    @property
    def button(self):
        return self._button

    def __repr__(self):
        return f"Activity(status={self.status}, header={self.header}, text={self.text})"

    @staticmethod
    def get_status(status_class: str):
        if "mee-icon-AddMedium" in status_class:
            value = Status.TODO
        elif "mee-icon-SkypeCircleCheck" in status_class:
            value = Status.DONE
        else:
            value = Status.INVALID
        return value

    def do_it(self):
        raise NotImplementedError


class StandardActivity(Activity):
    def do_it(self):
        pass

    def __repr__(self):
        return f"Standard{super().__repr__()}"


class QuizActivity(Activity):
    base_header = "Quiz"
    start_selector = "#rqStartQuiz"
    quiz_rounds = 3

    def __repr__(self):
        return f"Quiz{super().__repr__()}"

    def get_score(self, selector):
        try:
            value: str = self.driver.find_element_by_css_selector(selector).text
            current_score, max_score = value.strip().split("/")
            current_score, max_score = int(current_score), int(max_score)
        except exceptions.NoSuchElementException:
            current_score, max_score = None, None
        except ValueError:
            current_score, max_score = None, None
        return current_score, max_score

    def get_rounds(self):
        total_score_selector = "#btoHeadPanel > span.rqMenubar > span.rqText > span"
        current, total = self.get_score(total_score_selector)

        if total:
            rounds = (total - current) // 10
            assert rounds <= self.quiz_rounds
        else:
            rounds = self.quiz_rounds

        return rounds

    def do_it(self):
        try:
            self.driver.find_element_by_css_selector(self.start_selector).click()
        except exceptions.NoSuchElementException:
            pass

        try:
            container = self.driver.find_element_by_css_selector(
                "#currentQuestionContainer > div"
            )
            if container.get_attribute("class") == "textBasedMultiChoice":
                return self.do_it_four_choices()
            else:
                return self.do_it_eigth_choices()
        except exceptions.NoSuchElementException:
            return self.do_it_eigth_choices()

    def _do_it(self, answer_selectors):
        # rounds = self.get_rounds()
        rounds = self.quiz_rounds

        for quiz_round in range(rounds):
            time.sleep(2)

            for possible_sel in answer_selectors:
                time.sleep(1)
                try:
                    # click possibility tile
                    self.driver.find_element_by_css_selector(possible_sel).click()
                except exceptions.NoSuchElementException:
                    continue
                except exceptions.ElementNotInteractableException:
                    continue

    def do_it_four_choices(self):
        answer_selectors = [
            f"#currentQuestionContainer > div > div:nth-child({i})" for i in range(2, 6)
        ]
        return self._do_it(answer_selectors)

    def do_it_eigth_choices(self):
        answer_selectors = [f"#rqAnswerOption{i}" for i in range(8)]
        return self._do_it(answer_selectors)


class PollActivity(Activity):
    base_header = "Sondaggio"

    def __repr__(self):
        return f"Poll{super().__repr__()}"

    def do_it(self):
        selector = "#btoption0"
        self.driver.find_element_by_css_selector(selector).click()


class ThisOrThatActivity(Activity):
    base_header = "Questo o quello?"

    start_selector = "#rqStartQuiz"
    quiz_rounds = 10

    def __repr__(self):
        return f"ThisOrThat{super().__repr__()}"

    def do_it(self):
        # start activity
        try:
            self.driver.find_element_by_css_selector(self.start_selector).click()
            logging.info("Started quiz")
        except exceptions.NoSuchElementException:
            logging.info("Quiz already started")

        # answer selectors
        first_option_selector = "#rqAnswerOption0"
        # second_option_selector = "#rqAnswerOption1"

        for i in range(self.quiz_rounds):
            # TODO understand question and get right answer
            # TODO or get it right from some source
            answer = first_option_selector

            try:
                option = self.driver.find_element_by_css_selector(answer)
            except exceptions.NoSuchElementException:
                logging.warning("Element not found. Is the quiz already over?")
                break
            else:
                option.click()
                logging.info("Answer selected")
                time.sleep(2)


class Punchcard(Runnable, ABC):
    start_selector = "section > div > div > div > a"

    def __init__(self, driver: WebDriver, element: WebElement):
        self.driver = driver
        self.element = element
        self.text = element.get_attribute("aria-label")
        checkmarks = element.find_elements_by_css_selector("span.mee-icon")
        if not checkmarks:
            logging.warning(
                f"No checkmarks found for punchcard. Is it valid? (text={self.text})."
            )
            status = Status.INVALID
        else:
            if all(
                "checkmark" in checkmark.get_attribute("class")
                for checkmark in checkmarks
            ):
                status = Status.DONE
            else:
                status = Status.TODO
        logging.debug(f"Punchcard status is {status}")
        self.status = status
        self._button = element.find_element_by_css_selector(self.start_selector)

    @property
    def button(self):
        return self._button

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
