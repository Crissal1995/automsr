import enum
import logging
import random
import re
import time
from abc import ABC

from selenium.common import exceptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)


class Status(enum.IntEnum):
    TODO = 0
    DONE = 1
    INVALID = 2


class Runnable(ABC):
    name = "runnable"
    name_plural = "runnables"

    @property
    def button(self):
        raise NotImplementedError

    def do_it(self):
        raise NotImplementedError


class Activity(Runnable, ABC):
    name = "activity"
    name_plural = "activities"

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
        if any(
            value in status_class
            for value in ("mee-icon-AddMedium", "mee-icon-HourGlass")
        ):
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
    answers = []
    answers_4 = [f"rqAnswerOption{i}" for i in range(4)]
    answers_8 = [f"rqAnswerOption{i}" for i in range(8)]
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
        time.sleep(1)

        # try to press start button
        try:
            self.driver.find_element_by_id("rqStartQuiz").click()
            logger.debug("Started quiz")
        except exceptions.NoSuchElementException:
            logger.warning("Cannot find start button. Quiz already started?")

        # try to find question container
        # if not found, raise an exception
        try:
            self.driver.find_element_by_id("currentQuestionContainer")
        except exceptions.NoSuchElementException:
            logger.warning(
                "Cannot find question container. Quiz already finished? "
                "If runned with headless=true, try changing to false and retry"
            )
            return
        else:
            logger.debug("Question container found")

        try:
            container = self.driver.find_element_by_css_selector(
                "#currentQuestionContainer > div"
            )
            if container.get_attribute("class") == "textBasedMultiChoice":
                self.answers = self.answers_4
            else:
                self.answers = self.answers_8
        except exceptions.NoSuchElementException:
            self.answers = self.answers_8

        # finally execute quiz
        self._do_it()

    def _do_it(self):
        # rounds = self.get_rounds()
        rounds = self.quiz_rounds
        one_round_complete = False

        for quiz_round in range(rounds):
            logger.info(f"Round {quiz_round + 1}/{rounds} started")

            for answer_id in self.answers:
                time.sleep(1)
                try:
                    self.driver.find_element_by_id(answer_id).click()
                except exceptions.WebDriverException:
                    if not one_round_complete:
                        logger.warning(
                            f"Cannot click button with id: {answer_id}."
                            "If runned with headless=true, try changing to false and retry"
                        )
                        return
                    else:
                        continue

            one_round_complete = True


class PollActivity(Activity):
    base_header = "Sondaggio"

    def __repr__(self):
        return f"Poll{super().__repr__()}"

    def do_it(self):
        selector = "#btoption0"
        self.driver.find_element_by_css_selector(selector).click()


class ThisOrThatActivity(Activity):
    base_header = "Questo o quello?"

    quiz_rounds = 10

    def __repr__(self):
        return f"ThisOrThat{super().__repr__()}"

    def do_it(self):
        # let start popup appears on screen
        time.sleep(2)

        # try to press start button
        try:
            self.driver.find_element_by_id("rqStartQuiz").click()
            logger.debug("Started quiz")
        except exceptions.WebDriverException:
            logger.warning("Cannot find start button. ThisOrThat already started?")

        # try to find question container
        # if not found, raise an exception
        try:
            self.driver.find_element_by_id("currentQuestionContainer")
        except exceptions.WebDriverException:
            logger.warning(
                "Cannot find question container. Quiz already finished? "
                "If runned with headless=true, try changing to false and retry"
            )
            return
        else:
            logger.debug("Question container found")

        # answer selectors
        answers = ["rqAnswerOption0", "rqAnswerOption1"]

        is_last_round = False
        match_pattern = re.compile(r"(\d+)[^\d]*(\d+)")
        while not is_last_round:
            # regexp match rounds
            # two whiles for waiting changes
            rounds_elem = self.driver.find_element_by_class_name("bt_Quefooter")
            match = match_pattern.match(rounds_elem.text)
            while not match:
                time.sleep(1)
                rounds_elem = self.driver.find_element_by_class_name("bt_Quefooter")
                match = match_pattern.match(rounds_elem.text)
            current_round = int(match.group(1))
            logger.info(f"Starting round {current_round} / {self.quiz_rounds}")

            # if it's last round, next iteration won't happen
            if current_round == self.quiz_rounds:
                is_last_round = True

            # expected value: 25 points out of 50
            answer = random.choice(answers)
            answer_index = answers.index(answer)

            # click answer button
            answer_elem = self.driver.find_element_by_id(answer)
            answer_elem.click()
            logger.info(f"Answer {answer_index + 1} selected")
            time.sleep(2)


class Punchcard(Runnable, ABC):
    name = "punchcard"
    name_plural = "punchcards"

    start_selector = "section > div > div > div > a"

    def __init__(self, driver: WebDriver, element: WebElement):
        self.driver = driver
        self.element = element
        self.text = element.get_attribute("aria-label")
        checkmarks = element.find_elements_by_css_selector("span.mee-icon")
        if not checkmarks:
            logger.warning(
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
        logger.debug(f"Punchcard status is {status}")
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
        logger.debug(f"Found {len(punchcards)} punchcards actions inside {str(self)}")
        todo_punchcards = [
            punchcard for punchcard in punchcards if not self.is_complete(punchcard)
        ]
        logger.debug(
            f"Found {len(todo_punchcards)} todo punchcards actions inside {str(self)}"
        )
        home_win = self.driver.current_window_handle
        for i, punchcard in enumerate(todo_punchcards):
            punchcard.find_element_by_tag_name("a").click()
            logger.debug(f"Punchcard action no. {i + 1} completed")
            time.sleep(2)
            self.driver.switch_to.window(home_win)
