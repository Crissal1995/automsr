import csv
import enum
import logging
import pathlib
import random
import re
import time
from abc import ABC
from typing import Dict, List, Sequence, Union

from selenium.common import exceptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from msrewards.utility import get_date_str

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
        try:
            self._button = element.find_elements_by_css_selector(self.button_selector)[
                -1
            ]
        except IndexError:
            self.status = Status.INVALID

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
        retries = 3
        tts = 3

        for _ in range(retries):
            try:
                button = self.driver.find_element_by_id("btoption0")
                button.click()
            except exceptions.WebDriverException as e:
                logger.debug(f"Exception caught when doing {self}: {e}")
                self.driver.refresh()
                time.sleep(tts)
            else:
                break


class ThisOrThatCSV:
    """
    Class to manage CSV files for this or that activity.
    This CSV, if it exists, contains the answers for
    today's This Or That activity.

    The CSV headers are:
    - round (values go from 0 to 9)
    - selection (values can be
                -1: invalid
                0: first answer
                1: second answer)
    """

    name = f"thisorthat_{get_date_str()}.csv"
    headers = ["round", "selection"]
    answers: List[Dict[str, str]] = []
    _sorted = False

    ANSWERS_SIZE = 10  # must be equal to rounds size

    INVALID = -1
    FIRST = 0
    SECOND = 1

    def __init__(self):
        self.add_empty_answers()  # populate answers array with invalid questions
        if self.exists():  # but if csv file exists
            self.read_answers()  # populate answers from it

    def exists(self):
        return pathlib.Path(self.name).exists()

    def check_answers(self):
        if len(self.answers) != self.ANSWERS_SIZE:
            raise ValueError("Answers must be an array of 10 dict-element")

    def append_answer(self, answer: Sequence[Union[int, str]]):
        """Convert a generic answer to a correct dict answer"""
        if len(answer) != 2:
            raise ValueError("Answer must be a two-item sequence")
        answer_dict = {key: str(value) for (key, value) in zip(self.headers, answer)}
        self.answers.append(answer_dict)

    def override_answer(self, answer: Sequence[Union[int, str]]):
        """
        Ovveride a generic answer in the correct location,
        casting it as a dict answer
        """
        if len(answer) != 2:
            raise ValueError("Answer must be a two-item sequence")
        answer_dict = {key: str(value) for (key, value) in zip(self.headers, answer)}
        if self._sorted:
            ans_index = int(answer[0])
        else:
            ans_index = self.answers.index(
                [ans for ans in self.answers if ans[self.headers[0]] == str(answer[0])][
                    0
                ]
            )
        self.answers[ans_index] = answer_dict

    def get_answer(self, round_: Union[int, str]) -> Dict[str, str]:
        """Get an answer with round value"""
        if isinstance(round_, str):
            round_ = int(round_)

        if self._sorted:
            return self.answers[round_]
        else:
            return [ans for ans in self.answers if ans[self.headers[0]] == str(round_)][
                0
            ]

    def sort_answers(self):
        def _sort(adict: Dict[str, str]) -> int:
            return int(adict[self.headers[0]])

        self.answers.sort(key=_sort)
        self._sorted = True

    def add_empty_answers(self, sort=True):
        answers_set = set([int(answer[self.headers[0]]) for answer in self.answers])
        missing_set = set(range(self.ANSWERS_SIZE)) - answers_set
        for round_ in missing_set:
            self.append_answer((round_, self.INVALID))
        self.check_answers()
        if sort:
            self.sort_answers()

    def write_answers(self):
        self.add_empty_answers()
        with open(self.name, "w", newline="") as f:
            writer = csv.DictWriter(f, self.headers)
            writer.writeheader()
            writer.writerows(self.answers)

    def read_answers(self):
        with open(self.name) as f:
            self.answers = []
            self._sorted = False

            reader = csv.DictReader(f)
            for row in reader:
                self.answers.append(row)
        self.add_empty_answers()


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
