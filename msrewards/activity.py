import enum
import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from msrewards import exceptions


class ActivityStatus(enum.IntEnum):
    TODO = 0
    DONE = 1
    INVALID = 2


class Activity:
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
            self.status = ActivityStatus.INVALID

        self.header = element.find_element_by_css_selector(self.header_selector).text
        self.text = element.find_element_by_css_selector(self.text_selector).text
        self.button = element.find_elements_by_css_selector(self.button_selector)[-1]

    def __repr__(self):
        return f"Activity(status={self.status}, header={self.header}, text={self.text})"

    @staticmethod
    def get_status(status_class: str):
        if "mee-icon-AddMedium" in status_class:
            value = ActivityStatus.TODO
        elif "mee-icon-SkypeCircleCheck" in status_class:
            value = ActivityStatus.DONE
        else:
            value = ActivityStatus.INVALID
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
        rounds = self.get_rounds()

        for quiz_round in range(rounds):
            time.sleep(2)

            for possible_sel in answer_selectors:
                try:
                    # click possibility tile
                    self.driver.find_element_by_css_selector(possible_sel).click()
                except exceptions.NoSuchElementException:
                    continue
                except exceptions.ElementNotInteractableException:
                    continue
                else:
                    time.sleep(0.8)

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

    def do_it(self):
        selector = "#btoption0"
        self.driver.find_element_by_css_selector(selector).click()


class ThisOrThatActivity(Activity):
    base_header = "Questo o quello?"

    def do_it(self):
        pass
