import datetime
import logging
import random
import re
import string
import time
from typing import Dict, Sequence, Tuple, Type

from selenium.common import exceptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

from automsr.activities import (
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
from automsr.exception import (
    AutomsrException,
    CannotCompleteActivityException,
    CannotRetrievePointsException,
    Detected2FAError,
    InvalidInputError,
    LessThanSixDailyActivitiesFoundException,
    NoDailyActivityFoundException,
)
from automsr.pages import (
    BannerCookiePage,
    BingLoginPage,
    CookieAcceptPage,
    LoginPage,
    TryMicrosoftBrowserPage,
)
from automsr.search import GoogleTakeoutSearchGenerator, RandomSearchGenerator
from automsr.search_takeout_parser import SearchTakeoutParser
from automsr.state import ActivityState, StateManager
from automsr.utility import (
    DriverCatcher,
    change_user_agent,
    config,
    get_driver,
    get_new_window,
    get_value_from_dictionary,
)
from automsr.utility import is_profile_used as ipu

logger = logging.getLogger(__name__)


class MicrosoftRewards:
    # URLs section
    url_rewards = "https://account.microsoft.com/rewards/"
    url_rewards_alt = "https://rewards.microsoft.com/"
    url_bing = "https://www.bing.com/"
    url_login = "https://login.live.com/login.srf"
    url_bing_searched = "https://www.bing.com/search?q=google"

    # Selectors section
    selector_daily_cards = (
        "#daily-sets > "
        "mee-card-group > div > mee-card > "
        "div > card-content > mee-rewards-daily-set-item-content > div"
    )
    selector_other_cards = (
        "#more-activities > "
        "div > mee-card.ng-scope.ng-isolate-scope.c-card > "
        "div > card-content > mee-rewards-more-activities-card-item > div"
    )
    selector_punchcards = (
        "#punch-cards > mee-carousel > div >"
        " div:nth-child(4) > ul > li > a > mee-hero-item"
    )

    # User Agents section
    useragent_edge_win = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.49"
    )
    useragent_chrome_android = (
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
        implicitly_wait=3,
        is_profile_used=False,
    ):
        assert implicitly_wait > 0
        driver.implicitly_wait(implicitly_wait)
        self.driver = driver
        self.home = None
        self.credentials = credentials
        self.is_mobile = is_mobile

        self.state_manager = StateManager()

        if not is_profile_used:
            logger.info("Login started")
            self.login()
            logger.info("Login finished")
        else:
            logger.info("Profile provided, I assume you're already logged in there")

        self.go_to_home()

    def close(self):
        try:
            self.driver.quit()
        finally:
            logger.info("Chromedriver quitted")

        try:
            self.state_manager.close()
        finally:
            logger.info("State Manager closed")

    def __del__(self):
        self.close()

    def go_to(self, url):
        logger.debug(f"Go to URL: {url}")
        self.driver.get(url)

    def go_to_home(self):
        self.driver.get(self.url_rewards_alt)
        try:
            sign_in_selector = "a#raf-signin-link-id"
            self.driver.find_element_by_css_selector(sign_in_selector).click()
            logger.debug("Second MSR home step found")
        except exceptions.NoSuchElementException:
            logger.debug("No second MSR home step found")
        self.home = self.driver.current_window_handle

    def go_to_home_tab(self):
        if self.home:
            self.driver.switch_to.window(self.home)
        else:
            self.go_to_home()

    @classmethod
    def do_every_activity(cls, credentials: dict, **kwargs) -> str:
        # detect what to skip
        skip_activity = (
            config["automsr"]["skip_activity"] or credentials["skip_activity"]
        )
        skip_punchcard = (
            config["automsr"]["skip_punchcard"] or credentials["skip_punchcard"]
        )
        skip_search = config["automsr"]["skip_search"] or credentials["skip_search"]

        email = credentials["email"]

        # if both skips are true, exit function
        if all((skip_activity, skip_punchcard, skip_search)):
            msg = "Skipped everything"
            logger.info(msg)
            return msg

        # get chromium profile to use;
        # if missing, use selenium's default profile
        profile_dir = get_value_from_dictionary(credentials, ("profile_dir", "profile"))
        if profile_dir:
            kwargs.update(dict(profile_dir=profile_dir))

        # get to know if profile login should be used
        profile_root = config["selenium"]["profile_root"]
        is_profile_used = ipu(profile_root, profile_dir)

        # get a selenium driver
        driver = get_driver(**kwargs)

        with DriverCatcher(driver, take_screenshot_on_exception=False):
            # set its user agent to edge
            change_user_agent(driver, cls.useragent_edge_win)

            # create a rewards object
            rewards = cls(
                driver, credentials=credentials, is_profile_used=is_profile_used
            )

            # get points at the start of execution
            start_points_ok, start_points = rewards.get_safe_points()

            if start_points_ok:
                rewards.state_manager.insert_points(
                    email=email, points=start_points, timestamp=int(time.time())
                )

            # compute the message to send via mail
            messages = []

            # get retries
            retries = config["automsr"]["retry"]

            # execute activities
            if skip_activity:
                logger.warning("Skipping activity...")
            else:
                logger.warning("Starting activity...")
                rewards._execute_todo_runnables(Activity, retries=retries)

                # check if all activities are executed
                activities = rewards.state_manager.get_missing_activities(
                    email=email, date=datetime.date.today()
                )
                if activities:
                    n = len(activities)
                    msg = f"{n} activities were not executed!"
                    msg2 = ", ".join(str(activity) for activity in activities)

                    logger.error(msg)
                    logger.error(msg2)
                else:
                    msg = "All activities were executed!"
                    logger.info(msg)

                messages.append(msg)

            # execute punchcards
            if skip_punchcard:
                logger.warning("Skipping punchcards...")
            else:
                logger.warning("Starting punchcards...")
                rewards._execute_todo_runnables(Punchcard, retries=retries)

            # execute desktop searches
            if skip_search:
                logger.warning("Skipping daily search...")
            else:
                logger.warning("Starting daily search...")
                search_type = config["automsr"]["search_type"]
                rewards.execute_all_searches(search_type=search_type, retries=retries)

            # get points after execution
            end_points_ok, end_points = rewards.get_safe_points()

            # if both start and end are ok, compute delta
            delta = None
            if start_points_ok and end_points_ok:
                delta = end_points - start_points

            # if end points are ok, store them
            if end_points_ok:
                rewards.state_manager.insert_points(
                    email=email,
                    points=end_points,
                    timestamp=int(time.time()),
                    delta_points=delta,
                )

            # get true delta
            delta = rewards.state_manager.get_delta_points(email, datetime.date.today())

            msg = f"{delta} points accumulated."
            logger.info(msg)
            messages.append(msg)

            # get true final points, and compute how many (and which) gift cards you can get
            max_points = rewards.state_manager.get_final_points(
                email, datetime.date.today()
            )

            # close rewards and resources
            rewards.close()

            msg = f"Got {max_points} points."
            logger.info(msg)
            messages.append(msg)

            giftcards_str = rewards.get_gift_card_amounts_str(max_points)
            logger.info(giftcards_str)
            messages.append(giftcards_str)

            return "\n".join(messages)

    @staticmethod
    def get_gift_card_amounts(points: int, gift_card_prices: dict = None):
        """
        Return the amount of gift cards that can be redeemed on Microsoft Rewards.
        If no gift_card_prices is given, it will be used the default one
        for level 2 members, so:
           1860 points for a 2 € gift card,
           4650 points for a 5 € gift card,
           9300 points for a 10 € gift card.
        """
        gift_card_prices = gift_card_prices or {2: 1860, 5: 4650, 10: 9300}
        gift_card_amounts = {k: 0 for k in gift_card_prices}
        min_price = min(gift_card_prices.values())

        can_redeem = points >= min_price
        while can_redeem:
            for eur, price in sorted(gift_card_prices.items(), reverse=True):
                bought = points // price
                left = points % price
                if bought > 0:
                    points = left
                    gift_card_amounts[eur] = bought
            can_redeem = points >= min_price

        return gift_card_amounts

    @staticmethod
    def get_gift_card_amounts_str(points: int):
        amounts = MicrosoftRewards.get_gift_card_amounts(points)
        if not any(amounts.values()):
            return "Cannot redeem any gift card"

        # if I'm here, at least one gift card can be redeemed
        buffer = ["You can redeem "]
        for eur, amount in sorted(amounts.items(), reverse=True):
            if not amount:
                continue

            plural = "" if amount == 1 else "s"
            buffer += [f"{amount} {eur}€ gift card{plural}"]

        total_eur = sum(x * y for (x, y) in amounts.items())
        message = buffer[0] + ", ".join(buffer[1:]) + f". Total amount: {total_eur}€"
        return message

    def execute_all_searches(self, search_type: str, retries: int = 1):
        for i in range(retries):
            logger.debug(f"Searches retry {i+1} / {retries}")

            # change user agent to desktop
            change_user_agent(self.driver, self.useragent_edge_win)
            self.is_mobile = False

            # get points dict
            search_dict = self.check_missing_searches()

            # if every search dict is missing, exit
            if all(search_dict[ua]["missing"] == 0 for ua in ("desktop", "mobile")):
                logger.info("Searches completed")
                return

            # else execute desktop searches
            if search_dict["desktop"]["missing"] == 0:
                logger.info("Skipping desktop search, they are already done")
            else:
                limit = search_dict["desktop"]["missing"] // 3
                # to ensure we get all points, add an amount
                limit += 5
                self.execute_searches2(search_type=search_type, limit=limit)

            # change user agent to mobile
            change_user_agent(self.driver, self.useragent_chrome_android)
            self.is_mobile = True

            # and execute mobile searches
            if search_dict["mobile"]["missing"] == 0:
                logger.info("Skipping mobile search, they are already done")
            else:
                limit = search_dict["mobile"]["missing"] // 3
                # to ensure we get all points, add an offset
                limit += 5
                self.execute_searches2(search_type=search_type, limit=limit)

    def _store_activity_states(
        self, activities: Sequence[Activity], update_if_already_inserted=True
    ):
        email = self.credentials["email"]
        timestamp = int(time.time())

        for activity in activities:
            state = ActivityState(
                email=email,
                timestamp=timestamp,
                daily=activity.daily_set,
                status=activity.status.value,
                title=activity.header,
                description=activity.text,
            )

            # if this state's hash key is already found in DB, don't store it
            fetch_states = self.state_manager.fetch_states_filter_hash(
                "activity", state.hash  # type: ignore
            )
            if fetch_states:
                # if it's found and update should be made, do it
                if update_if_already_inserted:
                    self.state_manager.update_states_filter_hash(
                        "activity", state.hash, state.status  # type: ignore
                    )
                # , otherwise skip it
                else:
                    pass
            # , otherwise store it
            else:
                self.state_manager.insert_state(state)

    def _execute_todo_runnables(
        self, runnable_type: Type[Runnable], retries: int
    ) -> bool:
        """Execute to-do runnables, that can be activities or punchcards.
        Returns true if at least one runnable is executed, false otherwise"""
        self.go_to_home()

        missing = []
        any_todos = False

        if runnable_type is Activity:
            for _ in range(retries):
                activities = self.get_activities()
                self._store_activity_states(activities)

                missing = [
                    activity
                    for activity in activities
                    if activity.status == Status.TODO
                ]
                if not missing:
                    break
                else:
                    any_todos = True
                    self.execute_activities(missing)
                    self.go_to_home()

        elif runnable_type is Punchcard:
            for _ in range(retries):
                missing = self.get_free_todo_punchcards()
                if not missing:
                    break
                else:
                    any_todos = True
                    self.execute_punchcards(missing)
                    self.go_to_home()

        else:
            raise InvalidInputError(
                f"Provided class: '{runnable_type}'. "
                f"Only 'Activity' and 'Punchcard' classes are supported"
            )

        if missing:
            count = len(missing)
            word = runnable_type.name if count == 1 else runnable_type.name_plural
            msg = f"Cannot complete {count} {word}: {missing}"
            raise CannotCompleteActivityException(msg)
        elif any_todos:  # no missing, found at least one to-do runnable
            logger.info(f"All {runnable_type.name_plural} completed")
        else:  # no missing, found no to-do runnable
            logger.info(f"No todo {runnable_type.name_plural} found")

        # if false, no missing activity was found
        # else if true, all activities are completed
        # otherwise a runtime error is raised
        return any_todos

    def execute_activity(self, activity: Activity):
        return self.execute_activities([activity])

    def login(self):
        self.go_to(self.url_bing)
        try:
            CookieAcceptPage(self.driver).complete()
            logger.debug("Cookies accepted")
        except exceptions.NoSuchElementException:
            logger.debug("Cannot accept cookies")

        self.go_to(self.url_login)
        page = LoginPage(self.driver, self.url_login, self.credentials)
        page.complete()
        if page.check_2fa():
            raise Detected2FAError("2FA detected, cannot complete login")
        else:
            logger.info("Logged in")

        self.go_to(self.url_rewards)
        try:
            BannerCookiePage(self.driver).complete()
            logger.debug("Banner cookies accepted")
        except exceptions.WebDriverException:
            logger.debug("Cannot accept banner cookies")

        self.go_to(self.url_bing_searched)
        BingLoginPage(
            self.driver, self.url_login, self.credentials, self.is_mobile
        ).complete()
        logger.info("Login made on bing webpage")

        self.go_to(self.url_bing_searched)
        TryMicrosoftBrowserPage(self.driver).complete()

        time.sleep(1.5)

    def get_points(self, method: str = "dom") -> int:
        """Get points from Rewards Home with two possible methods,
        dom or animation. Dom crawls the page source, while animation
        get points from home (but has to wait for animation to finish)."""

        # converts to lowercase
        method = method.lower()

        # go to rewards home
        self.go_to_home()

        # wait a little to let the page load
        time.sleep(1)

        if method == "dom":
            source: str = self.driver.page_source
            match = re.search(r'"availablePoints":(\d+)', source)
            if not match:
                raise CannotRetrievePointsException(
                    "Cannot find 'availablePoints' in DOM!"
                )
            points = int(match.group(1))
        elif method == "animation":
            # wait a little to animation to finish
            time.sleep(3)
            text: str = self.driver.find_element_by_tag_name(
                "mee-rewards-user-status-balance"
            ).text
            logger.debug(f"User status balance text: {text}")
            points_str = text.split()[0]
            points = int(points_str.replace(",", "").replace(".", ""))
        else:
            raise InvalidInputError(
                f"Provided: '{method}'. Available methods are 'dom' and 'animation'"
            )

        logger.info(f"User status balance: {points}")
        return points

    def get_safe_points(
        self, method: str = "dom", retries: int = 3
    ) -> Tuple[bool, int]:
        """Get Rewards points in a finite number of retries.
        If no retry is good, then zero points will be returned.

        The return type is a tuple holding (FLAG, VALUE), where
        FLAG is true if points are got correctly, false otherwise;
        VALUE is the number of points got, or zero."""

        for retry in range(retries):
            logger.debug(f"Starting get_safe_points, retry {retry + 1}/{retries}")
            try:
                points = self.get_points(method)
            except Exception as e:
                logger.debug(f"An exception occurred: {e}")
            else:
                return True, points

        logger.warning("Cannot parse current user's points, defaulting to 0...")
        return False, 0

    def check_missing_searches(self) -> dict:
        # go to rewards page
        self.go_to_home()
        time.sleep(1.5)

        # open points popup
        self.driver.find_element_by_css_selector("#rx-user-status-action").click()
        time.sleep(2)

        # get searches
        cards_sel = "#userPointsBreakdown > div > div:nth-child(2) > div"
        cards = self.driver.find_elements_by_css_selector(cards_sel)

        if len(cards) < 2:
            cards_sel = ".pointsBreakdownCard"
            cards = self.driver.find_elements_by_css_selector(cards_sel)

        # cards should be 5:
        # desktop searches, mobile searches, edge bonus
        # points from ms store, activity points
        # assert len(cards) == 5

        # take first two cards (desktop and mobile searches)
        cards = cards[:2]

        # get text and points (as regexp)
        points_found = False
        points = []
        while not points_found:
            texts = [
                card.find_element_by_class_name("title-detail").text for card in cards
            ]
            points = [re.search(r"(\d+) / (\d+)", text) for text in texts]
            if all(points):
                points = [points_re.groups() for points_re in points]  # type: ignore
                points_found = True
            else:
                time.sleep(1)

        points_dict: Dict[str, Dict[str, int]] = dict(desktop={}, mobile={})

        for points_group, key in zip(points, points_dict):
            current_value = int(points_group[0])  # type: ignore
            max_value = int(points_group[1])  # type: ignore
            missing_value = max_value - current_value

            points_dict[key] = {
                "current": current_value,
                "max": max_value,
                "missing": missing_value,
            }

        return points_dict

    def execute_searches2(self, limit=None, search_type="random"):
        max_mobile = 20
        max_desktop = 30
        offset = 5

        if not limit:
            a = max_mobile if self.is_mobile else max_desktop
            a += offset
            b = a + offset
            # limit range is [MAX + OFFSET, MAX + 2*OFFSET]
            limit = random.randint(a, b)

        search_type_str = "Mobile" if self.is_mobile else "Desktop"
        logger.info(f"{search_type_str} searches will be executed {limit} times")

        if search_type == "takeout":
            search_generator = GoogleTakeoutSearchGenerator()
        elif search_type == "random":
            search_generator = RandomSearchGenerator()
        else:
            error_msg = "Invalid search_type provided"
            raise ValueError(error_msg)

        # go the bing page
        self.go_to(self.url_bing)

        # try to complete its login
        try:
            BingLoginPage(
                self.driver, self.url_login, self.credentials, self.is_mobile
            ).complete()
            logger.debug("Succesfully authenticated on BingPage")
        except exceptions.WebDriverException:
            logger.debug("Was already authenticated on BingPage")

        # ensure we're on bing search again
        self.go_to(self.url_bing)

        # take generator from search_generator
        # tts is not took as var because it's value can change
        generator = search_generator.query_gen()

        # and then send the query to the input field
        selector = "#sb_form_q"

        # safe selection of input form
        retries = 5
        input_field_found = False
        input_field = None
        last_exception = None

        while not input_field_found and retries > 0:
            try:
                input_field = self.driver.find_element_by_css_selector(selector)
            except exceptions.WebDriverException as e:
                retries -= 1  # decrease retries
                last_exception = e  # save exception
                time.sleep(1)  # then refresh the page
                self.driver.refresh()
            else:
                input_field_found = True

        if not input_field:
            raise last_exception or AutomsrException(
                f"Cannot find input field (selector={selector})"
            )

        # if I have the input field, then proceed
        input_field.send_keys(next(generator))
        input_field.send_keys(Keys.ENTER)

        time.sleep(search_generator.tts)

        for i in tqdm(range(limit)):
            logger.debug(f"Search {i + 1}/{limit}")

            # must search again input field because of page reloading
            input_field = self.driver.find_element_by_css_selector(selector)

            input_field.send_keys(next(generator))
            input_field.send_keys(Keys.ENTER)

            time.sleep(search_generator.tts)

        logger.info("Searches completed")

    def execute_searches(self, limit=None, search_type="random"):
        max_mobile = 20
        max_desktop = 30
        offset = 10

        if not limit:
            a = max_mobile if self.is_mobile else max_desktop
            a += offset
            b = a + offset
            # limit range is [MAX + OFFSET, MAX + 2*OFFSET]
            limit = random.randint(a, b)

        search_type_str = "Mobile" if self.is_mobile else "Desktop"
        logger.info(f"{search_type_str} searches will be executed {limit} times")

        if search_type == "takeout":
            self.takeout_searcher(limit)
        elif search_type == "random":
            self.random_searcher(limit)
        else:
            error_msg = (
                f"Invalid search_type provided: '{search_type}'. "
                "Available are 'takeout' or 'random'"
            )
            raise ValueError(error_msg)

    def takeout_searcher(self, limit):
        for _ in tqdm(range(limit)):
            try:
                BingLoginPage(
                    self.driver, self.url_login, self.credentials, self.is_mobile
                ).complete()
                logger.debug("Succesfully authenticated on BingPage")
            except exceptions.NoSuchElementException:
                logger.debug("Was already authenticated on BingPage")

            parser = SearchTakeoutParser("./my_activities.json")
            random_key = random.randint(0, parser.activity_count)
            word = parser.get_query(random_key)
            word_length = len(word)

            logger.debug(f"Word to be searched (lenght: {word_length}): {word}")

            self.go_to(self.url_bing)

            input_field = self.driver.find_element_by_css_selector("#sb_form_q")
            input_field.send_keys(word)
            input_field.send_keys(Keys.ENTER)

            sleep_time = random.randint(10, 60)
            logger.debug(f"Next search after {sleep_time}s")

            time.sleep(sleep_time)

    def random_searcher(self, limit):
        max_word_length = 70
        alphabet = string.ascii_lowercase

        word_length = random.randint(limit, max_word_length)
        word = "".join([random.choice(alphabet) for _ in range(word_length)])

        logger.debug(f"Word to be searched (lenght: {word_length}): {word}")

        # go the bing page
        self.go_to(self.url_bing)

        # try to complete its login
        try:
            BingLoginPage(
                self.driver, self.url_login, self.credentials, self.is_mobile
            ).complete()
            logger.debug("Succesfully authenticated on BingPage")
        except exceptions.WebDriverException:
            logger.debug("Was already authenticated on BingPage")

        # ensure we're on bing search again
        self.go_to(self.url_bing)

        # and then send entire word
        selector = "#sb_form_q"

        input_field = self.driver.find_element_by_css_selector(selector)
        input_field.send_keys(word)
        input_field.send_keys(Keys.ENTER)

        time.sleep(1)

        for i in tqdm(range(limit)):
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

    def _execute(
        self, runnables: Sequence[Runnable], runnable_type: str
    ) -> Sequence[Runnable]:
        """
        runnables: The list of Runnable objects to execute (activities or punchcards)
        runnable_type: The type of the runnables to execute ("activity" or "punchcard")
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

        # try to dismiss bottom span once for every execution
        TryMicrosoftBrowserPage(self.driver).complete()

        # create action chain
        actions = ActionChains(self.driver)

        for i, runnable in enumerate(runnables):
            logger.info(f"Starting runnable {singular} {i+1}/{length}: {str(runnable)}")

            # go to homepage
            self.go_to_home_tab()

            # get old windows
            old_windows = set(self.driver.window_handles)

            # move to runnable element
            actions.move_to_element(runnable.element).perform()

            # start runnable
            runnable.start()

            # switch to page and let it load
            window = get_new_window(self.driver, old_windows)
            self.driver.switch_to.window(window)

            # refresh tab for some activities that don't always load
            self.driver.refresh()

            # let page load
            time.sleep(1)

            # execute the activity
            try:
                runnable.do_it()
                logger.info(f"{singular.title()} completed")
            except exceptions.WebDriverException as e:
                logger.error(f"{singular.title()} not completed - {e}")
                runnables_todo_again.append(runnable)

        return runnables_todo_again

    def execute_activities(self, activities: Sequence[Activity]):
        return self._execute(activities, "activity")

    def get_todo_activities(self, reverse: bool = False):
        """
        Return the to-do activities of the day,
        ordered from the first daily to the last other.

        reverse: If True, activities will be performed
        from last other to first daily. If False, default order.
        :return: The to-do activities of the day.
        """
        todos = [
            activity
            for activity in self.get_activities()
            if activity.status == Status.TODO
        ]
        logger.debug(f"Found {len(todos)} todo activities")

        # get order of activities as debug msg
        daily, other = "first daily", "last other"
        order = f"{daily} to {other}" if not reverse else f"{other} to {daily}"
        logger.debug(f"Activities order is {order}")

        if not todos:
            logger.debug("No todo activity found")
        elif reverse:
            todos = todos[::-1]
        return todos

    def get_activities(self):
        return self.get_daily_activities() + self.get_other_activities()

    def get_daily_activities(self):
        dailies = self._get_activities("daily")
        dailies_len = len(dailies)
        if dailies_len <= 0:
            raise NoDailyActivityFoundException("No daily activity found")
        elif dailies_len != 6:
            raise LessThanSixDailyActivitiesFoundException(
                "Daily activities should be 6:"
                " 3 for today's set and 3 for tomorrow's set"
            )
        else:
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

    def get_free_todo_punchcards(self, reverse: bool = False):
        punchcards = [
            punchcard
            for punchcard in self.get_free_punchcards()
            if punchcard.status == Status.TODO
        ]
        logger.debug(f"Found {len(punchcards)} free todo punchcards")
        if reverse:
            punchcards = punchcards[::-1]
        return punchcards

    def execute_todo_punchcards(self):
        return self.execute_punchcards(self.get_free_todo_punchcards())

    def execute_punchcard(self, punchcard: Punchcard):
        return self.execute_punchcards([punchcard])

    def execute_punchcards(self, punchcards: Sequence[Punchcard]):
        return self._execute(punchcards, "punchcard")

    def get_punchcards(self):
        paid_keywords = PaidPunchcard.keywords

        punchcards_list = []
        punchcards_elements_list = self.driver.find_elements_by_css_selector(
            self.selector_punchcards
        )
        logger.debug(f"Found {len(punchcards_elements_list)} punchcards")

        for element in punchcards_elements_list:
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
        daily_set = False
        if activity_type == "daily":
            selector = self.selector_daily_cards
            daily_set = True
        elif activity_type == "other":
            selector = self.selector_other_cards
        else:
            raise InvalidInputError(
                f"Provided: '{activity_type}'. Valid types are 'daily' and 'other'"
            )

        activities_list = []

        for element in self.driver.find_elements_by_css_selector(selector):
            # find card header of element
            header: str = element.find_element_by_css_selector(
                Activity.header_selector
            ).text
            logger.debug(f"Activity header text is: {header}")

            header_cmp = header.lower().strip()

            # cast right type to elements
            if ThisOrThatActivity.base_header.lower() in header_cmp:
                activity = ThisOrThatActivity(
                    driver=self.driver, element=element, daily_set=daily_set
                )
                logger.debug("This or That Activity found")
            elif PollActivity.base_header.lower() in header_cmp:
                activity = PollActivity(
                    driver=self.driver, element=element, daily_set=daily_set
                )
                logger.debug("Poll Activity found")
            elif QuizActivity.base_header.lower() in header_cmp:
                activity = QuizActivity(
                    driver=self.driver, element=element, daily_set=daily_set
                )
                logger.debug("Quiz Activity found")
            else:
                activity = StandardActivity(
                    driver=self.driver, element=element, daily_set=daily_set
                )
                logger.debug("Standard activity found")
            logger.debug(str(activity))

            # append to activites
            activities_list.append(activity)

        return activities_list
