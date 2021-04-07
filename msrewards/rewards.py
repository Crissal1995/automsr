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

from msrewards.activities import (
    Activity,
    FreePunchcard,
    PaidPunchcard,
    PollActivity,
    Punchcard,
    QuizActivity,
    Runnable,
    StandardActivity,
    Status,
    ThisOrThatActivity,
)
from msrewards.pages import BannerCookiePage, BingLoginPage, CookieAcceptPage, LoginPage


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

    punchcard_selector = (
        "#punch-cards > mee-carousel > div > div:nth-child(4) > ul > li > mee-hero-item"
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
        try:
            self.driver.quit()
        except (exceptions.WebDriverException, Exception):
            logging.warning("Driver was already quitted")
        logging.info("Chromedriver quitted")

    @staticmethod
    def get_chrome_options(**kwargs):
        is_headless = kwargs.get("headless", True)

        chrome_options = Options()
        chrome_options.add_argument("no-sandbox")
        chrome_options.add_argument("ignore-certificate-errors")
        chrome_options.add_argument("allow-running-insecure-content")

        if is_headless:
            chrome_options.add_argument("headless")
            if sys.platform in ("win32", "cygwin"):
                # fix for windows platforms
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
        else:
            self.go_to_home()

    def save_cookies(self, cookies_json_fp=default_cookies_json_fp):
        json.dump(self.driver.get_cookies(), open(cookies_json_fp, "w"))

    def restore_cookies(self, cookies_json_fp=default_cookies_json_fp):
        cookies_json = json.load(open(cookies_json_fp))
        self.driver.delete_all_cookies()
        for cookie in cookies_json:
            self.driver.add_cookie(cookie)
        self.driver.get(self.rewards_url)

    @classmethod
    def daily_activities(cls, credentials: dict, **kwargs):
        options = cls.get_chrome_options(**kwargs)

        # standard points from activity
        driver = Chrome(options=options)

        rewards = cls(driver, credentials=credentials)
        rewards.go_to_home()
        rewards.execute_todo_activities()

        rewards.go_to_home()
        rewards.execute_todo_punchcards()

        driver.quit()

    @classmethod
    def daily_searches(cls, credentials: dict, **kwargs):
        # points from searches
        uas = [cls.edge_win_ua, cls.chrome_android_ua]

        for ua, is_mobile in zip(uas, (False, True)):
            options = cls.get_chrome_options(**kwargs)
            options.add_argument(f"user-agent={ua}")

            driver = Chrome(options=options)
            rewards = cls(driver, credentials, is_mobile=is_mobile)
            rewards.execute_searches()
            driver.quit()

    def execute_activity(self, activity: Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to(self.bing_url)
        try:
            CookieAcceptPage(self.driver).complete()
            logging.info("Cookies accepted")
        except exceptions.NoSuchElementException:
            logging.info("Cannot accept cookies")

        self.go_to(self.login_url)
        LoginPage(driver=self.driver, credentials=self.credentials).complete()
        logging.info("Logged in")

        self.go_to(self.rewards_url)
        try:
            BannerCookiePage(self.driver).complete()
            logging.info("Banner cookies accepted")
        except exceptions.NoSuchElementException:
            logging.info("Cannot accept banner cookies")

        self.go_to(self.bing_searched_url)
        BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
        logging.info("Login made on bing webpage")

        time.sleep(0.5)

    def execute_searches(self, limit=None):
        alphabet = string.ascii_lowercase
        MAX_SEARCH_DESKTOP = 30
        MAX_SEARCH_MOBILE = 20
        OFFSET_SEARCH = 10
        MAX_WORD_LENGTH = 70

        if not limit:
            a = MAX_SEARCH_MOBILE if self.is_mobile else MAX_SEARCH_DESKTOP
            a += OFFSET_SEARCH
            b = a + OFFSET_SEARCH
            # limit range is [MAX + OFFSET, MAX + 2*OFFSET]
            limit = random.randint(a, b)

        logging.info(f"Searches will be executed {limit} times")

        word_length = random.randint(limit, MAX_WORD_LENGTH)
        word = "".join([random.choice(alphabet) for _ in range(word_length)])

        logging.info(f"Word length be searched: {word_length}")

        self.go_to(self.bing_url)

        input_field = self.driver.find_element_by_css_selector("#sb_form_q")
        input_field.send_keys(word)
        input_field.send_keys(Keys.ENTER)

        time.sleep(1)

        try:
            BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
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

    def get_new_window(self, old_windows):
        # get new windows
        new_windows = set(self.driver.window_handles)

        # get window as diff between new and old windows
        # if the set is empty (pop fails), then the button
        # opened in current window handle
        try:
            window = new_windows.difference(old_windows).pop()
            logging.debug("Link opened in new window")
        except KeyError:
            window = self.driver.current_window_handle
            logging.debug("Link opened in same window")

        return window

    def _execute(self, runnables: [Runnable], runnable_type: str):
        """
        :param runnables: The list of Runnable objects to execute (activities or punchcards)
        :param runnable_type: The type of the runnables to execute ("activity" or "punchcard")
        :return: The list of runnables not completed
        """
        assert runnable_type in ("activity", "punchcard"), "Wrong runnable provided"
        name_dict = {
            "activity": ("activity", "activities"),
            "punchcard": ("punchcard", "punchcards"),
        }
        singular, plural = name_dict[runnable_type]

        runnables_todo_again = []

        logging.info(f"Start execute {plural}")

        length = len(runnables)
        if length == 0:
            logging.info(f"No {singular} found")
            return []

        for i, runnable in enumerate(runnables):
            logging.info(f"Starting {singular} {i+1}/{length}: {str(runnable)}")

            # go to homepage
            self.go_to_home_tab()

            # get old windows
            old_windows = set(self.driver.window_handles)

            # start runnable
            runnable.button.click()

            # switch to page and let it load
            window = self.get_new_window(old_windows)
            self.driver.switch_to.window(window)
            time.sleep(2)

            # try to log in via bing
            try:
                BingLoginPage(self.driver, self.is_mobile).complete()
                logging.warning("Bing login was required, but is done.")

                # add the runnable to the ones to do again
                runnables_todo_again.append(runnable)
                continue
            except exceptions.WebDriverException:
                logging.debug("No bing login required")

            # execute the activity
            try:
                runnable.do_it()
                logging.info(f"{singular.title()} completed")
            except (exceptions.WebDriverException, Exception) as e:
                logging.error(f"{singular.title()} not completed - {e}")
                runnables_todo_again.append(runnable)

        return runnables_todo_again

    def execute_activities(self, activities: [Activity]):
        return self._execute(activities, "activity")

    def get_todo_activities(self):
        todos = [
            activity
            for activity in self.get_activities()
            if activity.status == Status.TODO
        ]
        logging.info(f"Found {len(todos)} todo activities")
        if not todos:
            logging.warning("No todo activity found!")
        return todos

    def get_activities(self):
        return self.get_daily_activities() + self.get_other_activities()

    def get_daily_activities(self):
        dailies = self._get_activities("daily")
        dailies_len = len(dailies)
        assert dailies_len > 0, "No daily found"
        assert dailies_len == 6, "Dailies should be 6: 3 today and 3 tomorrow sets"
        # take first three, the current daily
        return dailies[:3]

    def get_other_activities(self):
        return self._get_activities("other")

    def get_free_punchcards(self):
        punchcards = [
            punchcard
            for punchcard in self.get_punchcards()
            if isinstance(punchcard, FreePunchcard)
        ]
        logging.debug(f"Found {len(punchcards)} free punchcards")
        return punchcards

    def get_free_todo_punchcards(self):
        punchcards = [
            punchcard
            for punchcard in self.get_free_punchcards()
            if punchcard.status == Status.TODO
        ]
        logging.debug(f"Found {len(punchcards)} free todo punchcards")
        return punchcards

    def execute_todo_punchcards(self):
        return self.execute_punchcards(self.get_free_todo_punchcards())

    def execute_punchcard(self, punchcard: Punchcard):
        return self.execute_punchcards([punchcard])

    def execute_punchcards(self, punchcards: [Punchcard]):
        return self._execute(punchcards, "punchcard")

    def get_punchcards(self):
        paid_keywords = PaidPunchcard.keywords

        punchcards_list = []

        for element in self.driver.find_elements_by_css_selector(
            self.punchcard_selector
        ):
            # get element text from aria-label attribute
            text = element.get_attribute("aria-label").lower()

            # check from text if the punchcard is free or paid
            # TODO is there a better way?
            if any(word in text for word in paid_keywords):
                logging.debug("Paid punchcard found")
                punchcard = PaidPunchcard(driver=self.driver, element=element)
            else:
                logging.debug("Free punchcard found")
                punchcard = FreePunchcard(driver=self.driver, element=element)

            punchcards_list.append(punchcard)

        return punchcards_list

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
            header = element.find_element_by_css_selector(Activity.header_selector).text

            logging.debug(f"Activity header found: {header}")

            # cast right type to elements
            if ThisOrThatActivity.base_header in header:
                activity = ThisOrThatActivity(driver=self.driver, element=element)
                logging.debug("This or That Activity found")
            elif PollActivity.base_header in header:
                activity = PollActivity(driver=self.driver, element=element)
                logging.debug("Poll Activity found")
            elif QuizActivity.base_header in header:
                activity = QuizActivity(driver=self.driver, element=element)
                logging.debug("Quiz Activity found")
            else:
                activity = StandardActivity(driver=self.driver, element=element)
                logging.debug("Standard activity found")
            logging.debug(str(activity))

            # append to activites
            activities_list.append(activity)

        return activities_list
