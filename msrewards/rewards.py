import json
import random
import string
import time

from selenium.common import exceptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from msrewards import pages
from msrewards.activity import (
    Activity,
    ActivityStatus,
    PollActivity,
    QuizActivity,
    StandardActivity,
    ThisOrThatActivity,
)


class MicrosoftRewards:
    rewards_url = "https://account.microsoft.com/rewards/"
    bing_url = "https://www.bing.com/"
    login_url = "https://login.live.com/login.srf"
    bing_searched_url = (
        "https://www.bing.com/search?q=rick+astley+never+gonna+give+you+up"
    )

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

    edge_win_ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
    )
    chrome_android_ua = (
        "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157"
        " Mobile Safari/537.36"
    )

    def __init__(
        self,
        driver: WebDriver,
        credentials: dict,
        *,
        is_mobile=False,
        implicitly_wait=7,
        cookies_json_fp=default_cookies_json_fp,
    ):
        assert implicitly_wait > 0
        driver.implicitly_wait(implicitly_wait)
        self.driver = driver
        self.home = None
        self.cookies_json_fp = cookies_json_fp
        self.credentials = credentials
        self.is_mobile = is_mobile
        self.login()

    def __del__(self):
        self.driver.quit()

    def go_to(self, url):
        self.driver.get(url)

    def go_to_home(self):
        self.driver.get(self.rewards_url)
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
        self.driver.get(self.rewards_url)

    @classmethod
    def daily_activities(cls, credentials: dict):
        # standard points from activity
        driver = Chrome()

        rewards = cls(driver, credentials=credentials)
        rewards.go_to_home()
        rewards.execute_todo_activities()

        driver.quit()

    @classmethod
    def daily_searches(cls, credentials: dict):
        # points from searches
        uas = [cls.edge_win_ua, cls.chrome_android_ua]

        for ua, is_mobile in zip(uas, (False, True)):
            options = Options()
            options.add_argument(f"user-agent={ua}")

            driver = Chrome(options=options)
            rewards = cls(driver, credentials, is_mobile=is_mobile)
            rewards.execute_searches()
            driver.quit()

    def execute_activity(self, activity: Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to(self.bing_url)
        pages.CookieAcceptPage(self.driver).complete()

        self.go_to(self.login_url)
        pages.LoginPage(driver=self.driver, credentials=self.credentials).complete()

        self.go_to(self.rewards_url)
        pages.BannerCookiePage(self.driver).complete()

        self.go_to(self.bing_searched_url)
        pages.BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
        time.sleep(0.5)

    def execute_searches(self, limit=None):
        alphabet = string.ascii_letters + string.digits
        if not limit:
            limit = random.randint(90, 120)
        self.go_to(self.bing_url)

        word_length = random.randint(100, 150)
        word = "".join([random.choice(alphabet) for _ in range(word_length)])

        input_field = self.driver.find_element_by_css_selector("#sb_form_q")
        input_field.send_keys(word)
        input_field.send_keys(Keys.ENTER)

        time.sleep(1)

        try:
            pages.BingLoginPage(self.driver).complete()
        except exceptions.NoSuchElementException:
            pass

        for i in range(limit):
            time.sleep(0.5)
            input_field = self.driver.find_element_by_css_selector("#sb_form_q")
            input_field.send_keys(Keys.BACKSPACE)
            input_field.send_keys(Keys.ENTER)

    def execute_todo_activities(self):
        return self.execute_activities(self.get_todo_activities())

    def execute_activities(self, activities):
        # while instead of for to do again activity if something goes wrong
        i = 0
        while i < len(activities):
            # take activity i
            activity = activities[i]

            # get old windows
            old_windows = set(self.driver.window_handles)

            # start activity
            activity.button.click()

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
            try:
                activity.do_it(driver=self.driver)
                # increment counter and goes to next activity
                i += 1
            # still login error
            except exceptions.NoSuchElementException:
                login_sel = "body > div.simpleSignIn > div.signInOptions > span > a"
                self.driver.find_element_by_css_selector(login_sel).click()

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
                activity = ThisOrThatActivity(driver=self.driver, element=element)
            elif PollActivity.base_header in header:
                activity = PollActivity(driver=self.driver, element=element)
            elif QuizActivity.base_header in header:
                activity = QuizActivity(driver=self.driver, element=element)
            else:
                activity = StandardActivity(driver=self.driver, element=element)

            # append to activites
            activities.append(activity)

        return activities
