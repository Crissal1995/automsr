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


class ThisOrThatAnswer(enum.Enum):
    MISSING = -1
    FIRST = 0
    SECOND = 1

    @classmethod
    def from_value(cls, value: int):
        values = {
            -1: cls.MISSING,
            0: cls.FIRST,
            1: cls.SECOND,
        }
        return values[value]


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

    ANSWERS_SIZE = 10  # must be equal to rounds size

    name = f"thisorthat_{get_date_str()}.csv"
    headers = ["round", "answer"]
    answers: List[ThisOrThatAnswer] = [ThisOrThatAnswer.MISSING] * ANSWERS_SIZE

    def __init__(self):
        if self.exists():  # if csv file exists
            self.read_answers()  # populate answers from it

    def exists(self):
        return pathlib.Path(self.name).exists()

    def override_answer(self, answer: Sequence[Union[int, ThisOrThatAnswer]]):
        """Ovveride an answer in its specified position"""
        index: int = answer[0]
        validity = answer[1]
        if isinstance(validity, int):
            validity = ThisOrThatAnswer.from_value(validity)
        self.answers[index] = validity

    def get_answer(self, round_index: int) -> ThisOrThatAnswer:
        """Get an answer from a round index value"""
        return self.answers[round_index]

    def _get_answers_dict(self) -> List[Dict[str, int]]:
        return [
            {
                key: value
                for (key, value) in zip(self.headers, [int(round_), int(answer.value)])
            }
            for (round_, answer) in enumerate(self.answers)
        ]

    def write_answers(self):
        """Writes answers to {name} csv file"""

        with open(self.name, "w", newline="") as f:
            writer = csv.DictWriter(f, self.headers)
            writer.writeheader()
            writer.writerows(self._get_answers_dict())

    def read_answers(self):
        """Reads answers from {name} csv file"""

        answers = [ThisOrThatAnswer.MISSING] * self.ANSWERS_SIZE

        with open(self.name) as f:
            reader = csv.DictReader(f)
            for row in reader:
                i = int(row[self.headers[0]])
                v = int(row[self.headers[1]])
                answers[i] = ThisOrThatAnswer.from_value(v)

        self.answers = answers


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

        # if I'm here, everything should be fine
        # so take the this or that csv manager
        tot_csv = ThisOrThatCSV()

        # answer selectors
        answers_sel = ["rqAnswerOption0", "rqAnswerOption1"]

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
            round_zerobased = current_round - 1
            logger.info(f"Starting round {current_round} / {self.quiz_rounds}")

            # if it's last round, next iteration won't happen
            if current_round == self.quiz_rounds:
                is_last_round = True

            # take the answer from the csv answers array
            # it's a validity enum object
            answer = tot_csv.get_answer(round_zerobased)

            # if the answer it's invalid, take a random shot
            if answer == ThisOrThatAnswer.MISSING:
                answer_sel = random.choice(answers_sel)
            # else take corresponding value in array
            else:
                answer_sel = answers_sel[int(answer.value)]

            # take index from array
            answer_index = answers_sel.index(answer_sel)

            # click answer button
            answer_elem = self.driver.find_element_by_id(answer_sel)
            answer_elem.click()
            logger.info(f"Answer {answer_index + 1} selected")
            time.sleep(1)

            # try to understand if the answer was correct or not
            sel = "#nextQuestionContainer > div > div > div > div.btQueInfo > div.bt_optionVS"

            # try-except to don't let this crash the code
            try:
                response: str = self.driver.find_element_by_css_selector(
                    sel
                ).get_attribute("class")
            except exceptions.WebDriverException:
                response = "undefined"

            if "wrong" in response.lower():
                logger.info("Wrong answer")
                if answer_index == int(ThisOrThatAnswer.FIRST.value):
                    correct_value = ThisOrThatAnswer.SECOND
                else:
                    correct_value = ThisOrThatAnswer.FIRST
            elif "correct" in response.lower():
                logger.info("Correct answer")
                correct_value = ThisOrThatAnswer.from_value(answer_index)
            else:
                logger.info("Cannot determine if correct or wrong answer")
                correct_value = ThisOrThatAnswer.MISSING
            tot_csv.override_answer((round_zerobased, correct_value))
            time.sleep(2)

        logger.info(f"Writing correct answers to {tot_csv.name}")
        tot_csv.write_answers()


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
