import json
import logging
import random
import string
import time

from selenium.common import exceptions
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
from msrewards.search_takeout_parser import SearchTakeoutParser
from msrewards.utility import change_user_agent, config, get_driver

logger = logging.getLogger(__name__)
missing_logger = logging.getLogger("missing")


def str_list(alist, joiner=", "):
    return joiner.join([str(elem) for elem in alist])


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
        logger.info("Login started")
        self.login()
        logger.info("Login finished")

    def __del__(self):
        try:
            self.driver.quit()
        except (exceptions.WebDriverException, Exception):
            logger.warning("Driver was already quitted")
        logger.info("Chromedriver quitted")

    def go_to(self, url):
        self.driver.get(url)
        logger.debug(f"Driver GET {url}")

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
    def do_every_activity(cls, credentials: dict, **kwargs):
        driver = get_driver(**kwargs)

        # set user agent to edge
        change_user_agent(driver, cls.edge_win_ua)

        rewards = cls(driver, credentials=credentials)

        # detect what to skip
        skip_activity = config["automsr"]["skip_activity"]
        skip_search = config["automsr"]["skip_search"]

        # execute runnables
        if skip_activity:
            logger.warning("Skipping activity...")
        else:
            logger.warning("Starting activity...")
            rewards._execute_todo_runnables("activity")
            rewards._execute_todo_runnables("punchcard")

        # execute desktop searches
        if skip_search:
            logger.warning("Skipping daily search...")
        else:
            logger.warning("Starting daily search...")
            search_type = config["automsr"]["search_type"]

            rewards.execute_searches(search_type=search_type)

            # change user agent to mobile
            change_user_agent(driver, cls.chrome_android_ua)
            rewards.is_mobile = True

            rewards.execute_searches(search_type=search_type)

    @classmethod
    def daily_activities(cls, credentials: dict, **kwargs):
        # standard points from activity
        driver = get_driver(**kwargs)

        # get a MicrosoftRewards object
        rewards = cls(driver, credentials=credentials)

        # and then execute runnables
        rewards._execute_todo_runnables("activity")
        rewards._execute_todo_runnables("punchcard")

        driver.quit()

    def _execute_todo_runnables(self, runnable_type: str):
        runnable_types = ("activity", "punchcard")
        errmsg = f"Wrong type provided ({runnable_type}). Valids are {runnable_types}"
        assert runnable_type in runnable_types, errmsg

        plural_dict = {
            "activity": "activities",
            "punchcard": "punchcards",
        }
        plural = plural_dict[runnable_type]
        singular = runnable_type

        self.go_to_home()

        if runnable_type == "activity":
            runnables = self.get_todo_activities()
        elif runnable_type == "punchcard":
            runnables = self.get_free_todo_punchcards()
        else:
            # future implementations, but it won't trigger
            raise NotImplementedError

        if not runnables:
            logger.info(f"No {singular} found...")
            return

        retries = config["automsr"]["retry"]
        for i in range(retries):
            logger.info(f"Execute {plural}, try {i + 1}/{retries}")
            runnables = self._execute(runnables, runnable_type)
            if not runnables:
                logger.info(f"All {plural} completed")
                break
            else:
                logger.warning(f"One or more {plural} weren't completed, try again...")

        if runnables:
            logger.error(
                f"Missing runnables (you should do them): - {str_list(runnables)}"
            )
            count = len(runnables)
            plural = "s" if count != 1 else ""
            missing_logger.error(
                f"Missing {count} runnable{plural} found, you have to do them on your own"
            )
            for runnable in runnables:
                missing_logger.error(str(runnable))

    @classmethod
    def daily_searches(cls, credentials: dict, **kwargs):
        user_agents = [
            dict(value=cls.edge_win_ua, is_mobile=False),
            dict(value=cls.chrome_android_ua, is_mobile=True),
        ]

        for user_agent in user_agents:
            kwargs.update(user_agent=user_agent["value"])
            driver = get_driver(**kwargs)
            rewards = cls(driver, credentials, is_mobile=user_agent["is_mobile"])
            search_type = config["automsr"]["search_type"]
            rewards.execute_searches(search_type=search_type)
            driver.quit()

    def execute_activity(self, activity: Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to(self.bing_url)
        try:
            CookieAcceptPage(self.driver).complete()
            logger.info("Cookies accepted")
        except exceptions.NoSuchElementException:
            logger.info("Cannot accept cookies")

        self.go_to(self.login_url)
        LoginPage(driver=self.driver, credentials=self.credentials).complete()
        logger.info("Logged in")

        self.go_to(self.rewards_url)
        try:
            BannerCookiePage(self.driver).complete()
            logger.info("Banner cookies accepted")
        except exceptions.NoSuchElementException:
            logger.info("Cannot accept banner cookies")

        self.go_to(self.bing_searched_url)
        BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
        logger.info("Login made on bing webpage")

        time.sleep(0.5)

    def execute_searches(self, limit=None, search_type="random"):
        MAX_MOBILE = 20
        MAX_DESKTOP = 30
        MAX_WORD_LENGTH = 70
        OFFSET = 10
        ALPHABET = string.ascii_lowercase

        if not limit:
            a = MAX_MOBILE if self.is_mobile else MAX_DESKTOP
            a += OFFSET
            b = a + OFFSET
            # limit range is [MAX + OFFSET, MAX + 2*OFFSET]
            limit = random.randint(a, b)

        logger.info(f"Searches will be executed {limit} times")

        if search_type == "takeout":
            self.takeout_searcher(limit)
        elif search_type == "random":
            self.random_searcher(limit, MAX_WORD_LENGTH, ALPHABET)
        else:
            error_msg = "Invalid search_type provided"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def takeout_searcher(self, limit):
        for i in range(limit):
            try:
                BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
                logger.info("Succesfully authenticated on BingPage")
            except exceptions.NoSuchElementException:
                logger.info("Was already authenticated on BingPage")

            parser = SearchTakeoutParser("./my_activities.json")
            random_key = random.randint(0, parser.n_of_search)
            word = parser.get_query(random_key)
            word_length = len(word)

            logger.debug(f"Word to be searched (lenght: {word_length}): {word}")

            self.go_to(self.bing_url)

            input_field = self.driver.find_element_by_css_selector("#sb_form_q")
            input_field.send_keys(word)
            input_field.send_keys(Keys.ENTER)

            sleep_time = random.randint(10, 60)
            logger.debug(f"Next search after {sleep_time}s")

            time.sleep(sleep_time)

    def random_searcher(self, limit, max_word_length, alphabet):
        word_length = random.randint(limit, max_word_length)
        word = "".join([random.choice(alphabet) for _ in range(word_length)])

        logger.debug(f"Word to be searched (lenght: {word_length}): {word}")

        self.go_to(self.bing_url)

        selector = "input[type=search]"

        input_field = self.driver.find_element_by_css_selector(selector)
        input_field.send_keys(word)
        input_field.send_keys(Keys.ENTER)

        time.sleep(1)

        try:
            BingLoginPage(self.driver, is_mobile=self.is_mobile).complete()
            logger.info("Succesfully authenticated on BingPage")
        except exceptions.NoSuchElementException:
            logger.info("Was already authenticated on BingPage")

        for i in range(limit):
            logger.debug(f"Search {i + 1}/{limit}")
            time.sleep(0.7)

            # must search again input field because of page reloading
            input_field = self.driver.find_element_by_css_selector(selector)

            input_field.send_keys(Keys.BACKSPACE)
            input_field.send_keys(Keys.ENTER)

        logger.info("Searches completed")

    def execute_todo_activities(self):
        logger.info("Execute todo activities start")

        activities_list = self.get_todo_activities()
        logger.info(f"{len(activities_list)} activities to do")

        return self.execute_activities(activities_list)

    def get_new_window(self, old_windows):
        # get new windows
        new_windows = set(self.driver.window_handles)

        # get window as diff between new and old windows
        # if the set is empty (pop fails), then the button
        # opened in current window handle
        try:
            window = new_windows.difference(old_windows).pop()
            logger.debug("Link opened in new window")
        except KeyError:
            window = self.driver.current_window_handle
            logger.debug("Link opened in same window")

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

        logger.info(f"Start execute {plural}")

        length = len(runnables)
        if length == 0:
            logger.info(f"No {singular} found")
            return []

        for i, runnable in enumerate(runnables):
            logger.info(f"Starting {singular} {i+1}/{length}: {str(runnable)}")

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
                logger.warning("Bing login was required, but is done.")

                # add the runnable to the ones to do again
                runnables_todo_again.append(runnable)
                continue
            except exceptions.WebDriverException:
                logger.debug("No bing login required")

            # execute the activity
            try:
                runnable.do_it()
                logger.info(f"{singular.title()} completed")
            except (exceptions.WebDriverException, Exception) as e:
                logger.error(f"{singular.title()} not completed - {e}")
                runnables_todo_again.append(runnable)

        return runnables_todo_again

    def execute_activities(self, activities: [Activity]):
        return self._execute(activities, "activity")

    def get_todo_activities(self, reverse: bool = True):
        """
        Return the to-do activities of the day,
        ordered from the first daily to the last other.
        :param reverse: If True, activities will be performed
        from last other to first daily. If False, default order.
        :return: The to-do activities of the day.
        """
        todos = [
            activity
            for activity in self.get_activities()
            if activity.status == Status.TODO
        ]
        logger.info(f"Found {len(todos)} todo activities")

        # get order of activities as debug msg
        daily, other = "first daily", "last other"
        order = f"{daily} to {other}" if not reverse else f"{other} to {daily}"
        logger.debug(f"Activities order is {order}")

        if not todos:
            logger.warning("No todo activity found!")
        elif reverse:
            todos = todos[::-1]
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
        logger.debug(f"Found {len(punchcards)} free punchcards")
        return punchcards

    def get_free_todo_punchcards(self):
        punchcards = [
            punchcard
            for punchcard in self.get_free_punchcards()
            if punchcard.status == Status.TODO
        ]
        logger.debug(f"Found {len(punchcards)} free todo punchcards")
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
                logger.debug("Paid punchcard found")
                punchcard = PaidPunchcard(driver=self.driver, element=element)
            else:
                logger.debug("Free punchcard found")
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

            logger.debug(f"Activity header found: {header}")

            # cast right type to elements
            if ThisOrThatActivity.base_header in header:
                activity = ThisOrThatActivity(driver=self.driver, element=element)
                logger.debug("This or That Activity found")
            elif PollActivity.base_header in header:
                activity = PollActivity(driver=self.driver, element=element)
                logger.debug("Poll Activity found")
            elif QuizActivity.base_header in header:
                activity = QuizActivity(driver=self.driver, element=element)
                logger.debug("Quiz Activity found")
            else:
                activity = StandardActivity(driver=self.driver, element=element)
                logger.debug("Standard activity found")
            logger.debug(str(activity))

            # append to activites
            activities_list.append(activity)

        return activities_list
