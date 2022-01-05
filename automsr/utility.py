import configparser
import datetime
import json
import logging
import os
import pathlib
from typing import Any, Optional, Sequence, Tuple, Union

from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.remote_connection import ChromeRemoteConnection
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Error class for invalid Credentials objects"""


def activity_skip(skip_str: str) -> Tuple[bool, ...]:
    """Function utility to know which activity,
    listed as (activities, punchcards, searches), is
    to be skipped.
    False means the activity should not be skipped,
    True otherwise.
    """

    skip_str = skip_str.lower().strip()

    if skip_str in ("yes", "all", "true"):
        return True, True, True
    if skip_str in ("no", "false"):
        return False, False, False

    skip_tuple = [False, False, False]
    skip_elems = [e.strip() for e in skip_str.split(",")]

    if any(kw in skip_elems for kw in ("activity", "activities")):
        skip_tuple[0] = True
    if any(kw in skip_elems for kw in ("punchcard", "punchcards")):
        skip_tuple[1] = True
    if any(kw in skip_elems for kw in ("search", "searches")):
        skip_tuple[2] = True

    return tuple(skip_tuple)


def is_profile_used(profile_root: str, profile_dir: str) -> bool:
    """Determines if the chrome profile should be used"""
    return bool(profile_root) and bool(profile_dir)


def get_value_from_dictionary(
    thedict: dict, keywords: Sequence[str], *, strict_non_false_value=False
) -> Optional[Any]:
    """Get value from dictionary, specifying a list of
    keywords that can be used to parse this value.
    If two or more keywords are provided, the first that matches
    a value will be used.

    Returns None if no keyword is found, else its value."""
    if isinstance(keywords, str):
        keywords = [keywords]

    for keyword in keywords:
        value = thedict.get(keyword)
        if strict_non_false_value and not value:
            continue
        if not strict_non_false_value and value is not None:
            return value
    return None


def get_datetime_str(
    datetime_obj: Union[datetime.datetime, datetime.date] = None, time: bool = False
):
    """Convert a datetime object to string"""
    if not datetime_obj:
        datetime_obj = datetime.datetime.today()
    s = str(datetime_obj)
    s = s.split(".")[0]  # remove ms
    s = s.replace("-", "_").replace(":", "_")
    if not time:
        s = s.split()[0]  # take only date part
    return s


def get_date_str(datetime_obj: Union[datetime.datetime, datetime.date] = None):
    return get_datetime_str(datetime_obj, False)


def get_options(**kwargs):
    global config

    options = Options()
    options.add_argument("no-sandbox")
    options.add_argument("ignore-certificate-errors")
    options.add_argument("allow-running-insecure-content")
    options.add_argument("disable-dev-shm-usage")
    options.add_argument("disable-gpu")

    profile_root = kwargs.get("profile_root") or config["selenium"]["profile_root"]
    profile_dir = kwargs.get("profile_dir")

    if profile_root and profile_dir:
        logger.info(f"Using profile '{profile_dir}' (root: {profile_root})")
        options.add_argument(f"--user-data-dir={profile_root}")
        options.add_argument(f"--profile-directory={profile_dir}")
    elif profile_dir:  # ignore only profile_root set
        raise ValueError(
            "Cannot use Chrome profile without 'profile_root' variable set in configuration"
        )

    ua = kwargs.get("user_agent")
    if ua:
        options.add_argument(f"user-agent={ua}")

    if kwargs.get("headless") or config["selenium"]["headless"]:
        options.add_argument("headless")

    if not config["selenium"]["enable_logging"]:
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

    return options


_default_config = {
    "automsr": {
        "retry": 3,
        "skip": "no",
        "credentials": "credentials.json",
        "search_type": "random",
        "email": "",
        "verbose": False,
    },
    "selenium": {
        "env": "local",
        "path": "chromedriver",
        "url": "http://localhost:4444/wd/hub",
        "headless": True,
        "logging": True,
        "profile_root": "",
    },
}


def get_config(cfg_fp: str = "", *, first_usage=False):
    parser = configparser.ConfigParser()

    # read defaults
    parser.read_dict(_default_config)

    # skip the read if it's first usage, 
    # found in this file with no path provided
    if not first_usage:
        # read file (can also be not found)
        if not cfg_fp:
            logger.warning("No config provided! Defaults will be used.")
        elif not parser.read(cfg_fp):
            logger.warning(f"Cannot read config from {cfg_fp}. Defaults will be used.")

    valid_selenium_envs = ("local", "remote")

    # get selenium options
    env = parser.get("selenium", "env")
    path = parser.get("selenium", "path")
    url = parser.get("selenium", "url")
    headless = parser.getboolean("selenium", "headless")
    enable_logging = parser.getboolean("selenium", "logging")
    profile_root = parser.get("selenium", "profile_root")

    # get automsr options
    skip = parser.get("automsr", "skip").lower()
    skip_activity, skip_punchcard, skip_search = activity_skip(skip)

    retry = parser.getint("automsr", "retry")
    credentials = parser.get("automsr", "credentials")
    search_type = parser.get("automsr", "search_type")
    email = parser.get("automsr", "email")
    verbose = parser.getboolean("automsr", "verbose")

    if env not in valid_selenium_envs:
        err = f"Invalid selenium env provided! Valid envs are: {valid_selenium_envs}"
        logger.error(err)
        raise ValueError(err)

    if retry < 1:
        msg = "Cannot have non-positive retries! Defaulting it to 1"
        logger.warning(msg)
        retry = 1

    return {
        "automsr": dict(
            skip=skip,
            skip_activity=skip_activity,
            skip_punchcard=skip_punchcard,
            skip_search=skip_search,
            retry=retry,
            credentials=credentials,
            search_type=search_type,
            email=email,
            verbose=verbose,
        ),
        "selenium": dict(
            env=env,
            path=path,
            url=url,
            headless=headless,
            enable_logging=enable_logging,
            profile_root=profile_root,
        ),
    }


# read one time and then use it
config = get_config(first_usage=True)


def get_driver(**kwargs):
    global config

    options = get_options(**kwargs)
    path = kwargs.get("path", config["selenium"]["path"])
    url = kwargs.get("url", config["selenium"]["url"])

    env = config["selenium"]["env"]

    if env == "local":
        driver = Chrome(executable_path=path, options=options)
    elif env == "remote":
        driver = Remote(
            command_executor=ChromeRemoteConnection(remote_server_addr=url),
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options,
        )
    else:
        raise NotImplementedError

    # expand driver full-screen
    driver.maximize_window()

    return driver


def change_user_agent(driver, new_user_agent: str):
    # go here to check commands
    # venv/Lib/site-packages/selenium/webdriver/chrome/remote_connection.py
    cmd = "Network.setUserAgentOverride"
    cmd_args = dict(userAgent=new_user_agent)

    driver.execute("executeCdpCommand", {"cmd": cmd, "params": cmd_args})

    actual_user_agent = str(driver.execute_script("return navigator.userAgent;"))
    assert actual_user_agent == new_user_agent, "Cannot set user-agent!"
    logger.debug(f"Changed user-agent to {new_user_agent}")


def test_environment(**kwargs):
    """Determine if current environment is correctly set"""
    driver = get_driver(**kwargs)
    driver.get("https://example.org/")
    driver.quit()
    logger.info("Selenium driver found!")


def get_credentials(credentials_fp):
    logger.debug("Start get_credentials function")

    errmsg = "Invalid credentials provided!"

    try:
        with open(credentials_fp) as fp:
            content = fp.read()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise e

    try:
        creds_list = json.loads(content)
    except json.JSONDecodeError:
        logger.error(errmsg + " Invalid Json provided")
        raise ValueError(errmsg)

    if not isinstance(creds_list, (list, tuple)):
        logger.error(errmsg + " Json must be a list of objects")
        raise ValueError(errmsg)

    for i, creds in enumerate(creds_list):
        creds_errmsg = f"{errmsg} - credentials no. {i}"
        if not isinstance(creds, dict):
            msg = f"{creds_errmsg} - Credentials must be object type"
            raise InvalidCredentialsError(msg)

        email = creds.get("email")
        password = creds.get("password")
        profile = get_value_from_dictionary(creds, ("profile", "profile_dir"))
        skip = creds.get("skip")

        if not email:
            msg = f"{creds_errmsg} - Missing email"
            raise InvalidCredentialsError(msg)

        if not password and not profile:
            msg = f"{creds_errmsg} - Missing password and profile!"
            raise InvalidCredentialsError(msg)

        if not skip:
            logger.warning("Skip value missing, defaults to 'no'")
            skip = "no"

        creds.update(skip=skip)

        skip_activity, skip_punchcard, skip_search = activity_skip(skip)
        creds.update(skip_activity=skip_activity)
        creds.update(skip_punchcard=skip_punchcard)
        creds.update(skip_search=skip_search)

        yield creds


def get_safe_credentials(credentials_fp):
    creds_gen = get_credentials(credentials_fp)

    while True:
        try:
            yield next(creds_gen)
        except InvalidCredentialsError:
            continue
        except StopIteration:
            break


def get_new_window(driver: Remote, old_windows):
    # get new windows
    new_windows = set(driver.window_handles)

    # get window as diff between new and old windows
    # if the set is empty (pop fails), then the button
    # opened in current window handle
    try:
        window = new_windows.difference(old_windows).pop()
        logger.debug("Link was opened in new window")
    except KeyError:
        window = driver.current_window_handle
        logger.debug("Link was opened in same window")

    return window


class DriverCatcher:
    """A context manager wrapper for selenium driver,
    used to catch exceptions and store information about it"""

    def __init__(
        self,
        driver: Remote,
        *,
        propagate_exception: bool = True,
        take_screenshot_on_exception: bool = True,
    ):
        self.driver = driver
        self.screen_dir = pathlib.Path("screenshots")
        self.propagate = propagate_exception
        self.take_screenshot = take_screenshot_on_exception

    def store_information_as_screenshot(self, fname: str = None):
        """Store the current driver screenshot in root dir with
        the specified fname.
        If no fname is provided, a timestamp will be used."""

        if not fname:
            # get current timestamp
            now = datetime.datetime.now()

            # convert it to a valid filename
            fname = str(now).replace(":", ".") + ".png"

        if not fname.endswith(".png"):
            fname += ".png"

        # concatenate it with rootdir
        path = self.screen_dir / fname

        # path to selenium func must be provided as absolute path
        fullpath = str(path.resolve())

        # save screenshot as png to path provided
        self.driver.get_screenshot_as_file(fullpath)

        return path

    def __enter__(self):
        if self.take_screenshot:
            os.makedirs(self.screen_dir, exist_ok=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Manage possible exceptions with the if-else branch.
        If the return is True, the exception is suppressed;
        otherwise is propagated."""

        if exc_type is None:
            return True
        else:
            logger.warning(
                f"An exception occurred! exc_type: {exc_type}, exc_val: {exc_val}"
            )
            if self.take_screenshot:
                path = self.store_information_as_screenshot()
                logger.warning(f"A screenshot was saved in {path}")

            # closes driver after screenshot is possibly taken
            self.driver.quit()

            return not self.propagate
