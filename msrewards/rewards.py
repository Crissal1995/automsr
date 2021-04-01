import json
import time

from selenium.webdriver.remote.webdriver import WebDriver

from msrewards.activity import (
    Activity,
    ActivityStatus,
    PollActivity,
    QuizActivity,
    StandardActivity,
    ThisOrThatActivity,
)
from msrewards.page import CookieAcceptPage, LoginPage


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

        self.login()

    def go_to(self, url):
        self.driver.get(url)
        self.driver.implicitly_wait(3)

    def go_to_home(self):
        self.driver.get(self.link)
        self.home = self.driver.current_window_handle

    def go_to_home_tab(self):
        if self.home:
            self.driver.switch_to.window(self.home)
        self.driver.implicitly_wait(3)

    def save_cookies(self, cookies_json_fp=default_cookies_json_fp):
        json.dump(self.driver.get_cookies(), open(cookies_json_fp, "w"))

    def restore_cookies(self, cookies_json_fp=default_cookies_json_fp):
        cookies_json = json.load(open(cookies_json_fp))
        self.driver.delete_all_cookies()
        for cookie in cookies_json:
            self.driver.add_cookie(cookie)
        self.driver.get(self.link)

    def execute_activity(self, activity: Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to("https://www.bing.com/")
        CookieAcceptPage(self.driver).complete()

        self.driver.find_element_by_css_selector("#id_s").click()
        LoginPage(self.driver).complete()

    def execute_todo_activities(self):
        return self.execute_activities(self.get_todo_activities())

    def execute_activities(self, activities):
        for activity in activities:
            # get old windows
            old_windows = set(self.driver.window_handles)

            # start activity
            activity.button.click()
            self.driver.implicitly_wait(2)

            # get new windows
            new_windows = set(self.driver.window_handles)

            # get window as diff between new and old windows
            # if the set is empty (pop fails), then the button
            # opened in current window handle
            try:
                window = new_windows.difference(old_windows).pop()
            except KeyError:
                window = self.driver.current_window_handle

            # switch to page and let it load
            self.driver.switch_to.window(window)
            time.sleep(2)

            # execute the activity
            activity.do_it(driver=self.driver)

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
            if ThisOrThatActivity.base_header in header:
                activity = ThisOrThatActivity(element)
            elif PollActivity.base_header in header:
                activity = PollActivity(element)
            elif QuizActivity.base_header in header:
                activity = QuizActivity(element)
            else:
                activity = StandardActivity(element)

            # append to activites
            activities.append(activity)

        return activities
