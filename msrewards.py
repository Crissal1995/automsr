import enum
import json

from selenium.common.exceptions import NoSuchElementException
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
        except NoSuchElementException:
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
    base_header = "Quiz bonus"

    def do_it(self, driver: WebDriver):
        pass


class PollActivity(Activity):
    base_header = "Sondaggio giornaliero"

    def do_it(self, driver: WebDriver):
        pass


class ThisOrThatActivity(Activity):
    base_header = "Questo o quello?"

    def do_it(self, driver: WebDriver):
        pass


class MicrosoftRewards:
    link = "https://account.microsoft.com/rewards/"
    default_cookies_json_fp = "cookies.json"

    daily_card_selector = (
        "#daily-sets > "
        "mee-card-group > div > mee-card > "
        "div > card-content > mee-rewards-daily-set-item-content > div"
    )

    other_card_selector = (
        "#more-activities > "
        "div > mee-card.ng-scope.ng-isolate-scope.c-card > "
        "div > card-content > mee-rewards-more-activities-card-item > div"
    )

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.home = None

    def go_to_home(self):
        self.driver.get(self.link)
        self.home = self.driver.current_window_handle

    def go_to_home_tab(self):
        if self.home:
            self.driver.switch_to.window(self.home)

    def save_cookies(self, cookies_json_fp=default_cookies_json_fp):
        json.dump(self.driver.get_cookies(), open(cookies_json_fp, "w"))

    def restore_cookies(self, cookies_json_fp=default_cookies_json_fp):
        cookies_json = json.load(open(cookies_json_fp))
        self.driver.delete_all_cookies()
        for cookie in cookies_json:
            self.driver.add_cookie(cookie)
        self.driver.get(self.link)

    def execute_activities(self, activities=None):
        if not activities:
            activities = self.get_todo_activities()

        for activity in activities:
            # start activity
            activity.button.click()

            # wait for the page to load
            self.driver.implicitly_wait(1)

            # execute the activity
            activity.do_it(self.driver)

            # and then return to the home
            self.go_to_home_tab()

    def get_todo_activities(self):
        return [
            activity
            for activity in self.get_activities()
            if activity.status == ActivityStatus.TODO
        ]

    def get_activities(self):
        return self.get_daily_activities() + self.get_other_activities()

    def get_daily_activities(self):
        dailies = self._get_activities("daily")
        # get first three cards (current)
        # the other three are next-day cards
        assert len(dailies) == 6
        return dailies[:3]

    def get_other_activities(self):
        return self._get_activities("other")

    def _get_activities(self, activity_type):
        if activity_type == "daily":
            selector = self.daily_card_selector
        elif activity_type == "other":
            selector = self.other_card_selector
        else:
            raise ValueError(
                f"Invalid activity type {activity_type}. Valids are 'daily' and 'other'"
            )

        activities = []

        for element in self.driver.find_elements_by_css_selector(selector):
            # find card header of element
            header = element.find_element_by_css_selector(Activity.header_selector).text

            # cast right type to elements
            if header in ThisOrThatActivity.base_header:
                activity = ThisOrThatActivity(element)
            elif header in PollActivity.base_header:
                activity = PollActivity(element)
            elif header in QuizActivity.base_header:
                activity = QuizActivity(element)
            else:
                activity = StandardActivity(element)

            # append to activites
            activities.append(activity)

        return activities
