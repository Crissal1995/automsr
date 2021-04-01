import enum
import time

from selenium.common import exceptions as selex
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


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

    def __init__(self, element: WebElement):
        self.element = element

        try:
            status_class = element.find_element_by_css_selector(
                self.status_selector
            ).get_attribute("class")
            self.status = Activity.get_status(status_class)
        except selex.NoSuchElementException:
            self.status = ActivityStatus.INVALID

        self.header = element.find_element_by_css_selector(self.header_selector).text
        self.text = element.find_element_by_css_selector(self.text_selector).text
        self.button = element.find_elements_by_css_selector(self.button_selector)[-1]

    @staticmethod
    def get_status(status_class: str):
        if "mee-icon-AddMedium" in status_class:
            value = ActivityStatus.TODO
        elif "mee-icon-SkypeCircleCheck" in status_class:
            value = ActivityStatus.DONE
        else:
            value = ActivityStatus.INVALID
        return value

    def do_it(self, driver: WebDriver):
        raise NotImplementedError


class StandardActivity(Activity):
    def do_it(self, driver: WebDriver):
        driver.implicitly_wait(5)


class QuizActivity(Activity):
    base_header = "Quiz"
    start_selector = "#rqStartQuiz"

    quiz_rounds = 3
    answer_selectors = [f"#rqAnswerOption{i}" for i in range(8)]

    def do_it(self, driver: WebDriver):
        def get_score(sel):
            try:
                value: str = driver.find_element_by_css_selector(sel).text
                current_score, max_score = value.strip().split("/")
                current_score, max_score = int(current_score), int(max_score)
            except selex.NoSuchElementException:
                current_score, max_score = None, None
            except ValueError:
                current_score, max_score = None, None
            return current_score, max_score

        try:
            driver.find_element_by_css_selector(self.start_selector).click()
        except selex.NoSuchElementException:
            pass

        total_score_selector = "#btoHeadPanel > span.rqMenubar > span.rqText > span"
        # round_score_selector = "#currentQuestionContainer > div > div.rqQuestion > span > span"

        current, total = get_score(total_score_selector)

        if total:
            rounds = (total - current) // 10
            assert rounds <= self.quiz_rounds
        else:
            rounds = self.quiz_rounds

        for quiz_round in range(rounds):
            time.sleep(2)

            for possible_sel in self.answer_selectors:
                try:
                    # click possibility tile
                    driver.find_element_by_css_selector(possible_sel).click()
                except selex.NoSuchElementException:
                    continue
                except selex.ElementNotInteractableException:
                    continue
                else:
                    time.sleep(0.5)


class PollActivity(Activity):
    base_header = "Sondaggio"

    def do_it(self, driver: WebDriver):
        selector = "#btoption0"
        driver.find_element_by_css_selector(selector).click()


class ThisOrThatActivity(Activity):
    base_header = "Questo o quello?"

    def do_it(self, driver: WebDriver):
        pass
