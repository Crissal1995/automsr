import json
import logging
import random
import string
import sys
import time

from selenium.common import exceptions
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from msrewards import activities, pages


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
        logging.info("Login started")
        self.login()
        logging.info("Login finished")

    def __del__(self):
        self.driver.quit()
        logging.info("Chromedriver quitted")

    @staticmethod
    def get_chrome_options(headless=True):
        chrome_options = Options()
        # chrome_options.add_argument("no-sandbox")
        # chrome_options.add_argument("ignore-certificate-errors")
        # chrome_options.add_argument("allow-running-insecure-content")
        if headless:
            chrome_options.add_argument("headless")
            if sys.platform in ("win32", "cygwin"):
                chrome_options.add_argument("disable-gpu")
        return chrome_options

    def go_to(self, url):
        self.driver.get(url)
        logging.debug(f"Driver GET {url}")

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
        options = cls.get_chrome_options()

        # standard points from activity
        driver = Chrome(options=options)

        rewards = cls(driver, credentials=credentials)
        rewards.go_to_home()
        rewards.execute_todo_activities()

        driver.quit()

    @classmethod
    def daily_searches(cls, credentials: dict):
        # points from searches
        uas = [cls.edge_win_ua, cls.chrome_android_ua]

        for ua, is_mobile in zip(uas, (False, True)):
            options = cls.get_chrome_options()
            options.add_argument(f"user-agent={ua}")

            driver = Chrome(options=options)
            rewards = cls(driver, credentials, is_mobile=is_mobile)
            rewards.execute_searches()
            driver.quit()

    def execute_activity(self, activity: activities.Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to(self.bing_url)
        try:
            pages.CookieAcceptPage(self.driver).complete()
            logging.info("Cookies accepted")
        except exceptions.NoSuchElementException:
            logging.info("Cannot accept cookies")

        self.go_to(self.login_url)
        pages.LoginPage(driver=self.driver, credentials=self.credentials).complete()
        logging.info("Logged in")

        self.go_to(self.rewards_url)
        try:
            pages.BannerCookiePage(self.driver).complete()
            logging.info("Banner cookies accepted")
        except exceptions.NoSuchElementException:
            logging.info("Cannot accept banner cookies")

        self.go_to(self.bing_searched_url)
        pages.BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
        logging.info("Login made on bing webpage")

        time.sleep(0.5)

    def execute_searches(self, limit=None):
        alphabet = string.ascii_letters + string.digits
        if not limit:
            limit = random.randint(90, 120)
        self.go_to(self.bing_url)

        logging.info(f"Searches will be executed {limit} times")

        word_length = random.randint(limit, 150)
        word = "".join([random.choice(alphabet) for _ in range(word_length)])

        logging.info(f"Word length be searched: {word_length}, word: {word}")

        input_field = self.driver.find_element_by_css_selector("#sb_form_q")
        input_field.send_keys(word)
        input_field.send_keys(Keys.ENTER)

        time.sleep(1)

        try:
            pages.BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
            logging.info("Succesfully authenticated on BingPage")
        except exceptions.NoSuchElementException:
            logging.info("Was already authenticated on BingPage")

        for i in range(limit):
            logging.info(f"Search {i + 1}/{limit}")
            time.sleep(0.5)

            # must search again input field because of page reloading
            input_field = self.driver.find_element_by_css_selector("#sb_form_q")

            input_field.send_keys(Keys.BACKSPACE)
            input_field.send_keys(Keys.ENTER)

    def execute_todo_activities(self):
        logging.info("Execute todo activities start")

        activities_list = self.get_todo_activities()
        logging.info(f"{len(activities_list)} activities to do")

        return self.execute_activities(activities_list)

    def execute_activities(self, activities_list):
        logging.info("Execute activities start")
        # while instead of for to do again activity if something goes wrong
        i = 0
        while i < len(activities_list):
            # take activity i
            activity = activities_list[i]

            logging.info(f"Activity {i + 1}/{len(activities_list)} - {str(activity)}")

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

            logging.info("Start activity")

            # execute the activity
            try:
                activity.do_it()
                # increment counter and goes to next activity
                i += 1
                logging.info("Activity completed")
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
            if activity.status == activities.ActivityStatus.TODO
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

        activities_list = []

        for element in self.driver.find_elements_by_css_selector(selector):
            # find card header of element
            header = element.find_element_by_css_selector(
                activities.Activity.header_selector
            ).text

            logging.debug(f"Activity header found: {header}")

            # cast right type to elements
            if activities.ThisOrThatActivity.base_header in header:
                activity = activities.ThisOrThatActivity(
                    driver=self.driver, element=element
                )
                logging.debug("This or That Activity found")
            elif activities.PollActivity.base_header in header:
                activity = activities.PollActivity(driver=self.driver, element=element)
                logging.debug("Poll Activity found")
            elif activities.QuizActivity.base_header in header:
                activity = activities.QuizActivity(driver=self.driver, element=element)
                logging.debug("Quiz Activity found")
            else:
                activity = activities.StandardActivity(
                    driver=self.driver, element=element
                )
                logging.debug("Standard activity found")
            logging.debug(str(activity))

            # append to activites
            activities_list.append(activity)

        return activities_list
