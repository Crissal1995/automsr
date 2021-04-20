import configparser
import json
import logging
import sys

from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.remote_connection import ChromeRemoteConnection
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Error class for invalid Credentials objects"""


possible_skips = (
    "no",
    "false",
    "all",
    "yes",
    "true",
    "search",
    "searches",
    "activity",
    "activities",
)


def activity_skip(skip_str: str) -> (bool, bool):
    """Function utility to know which activity,
    listed as (daily_activities, daily_searches), is
    to be skipped.
    False means the activity should not be skipped,
    True otherwise.
    """
    skip_dict = {
        "activity": (True, False),
        "search": (False, True),
        "yes": (True, True),
        "no": (False, False),
    }
    skip_dict["activities"] = skip_dict["activity"]
    skip_dict["searches"] = skip_dict["search"]
    skip_dict["all"] = skip_dict["yes"]
    skip_dict["true"] = skip_dict["yes"]
    skip_dict["false"] = skip_dict["no"]

    if any(kw not in skip_dict for kw in possible_skips):
        raise KeyError(f"Fix skip_dict! Missing some keys from {possible_skips}")

    return skip_dict[skip_str]


def get_options(**kwargs):
    global config

    options = Options()
    options.add_argument("no-sandbox")
    options.add_argument("ignore-certificate-errors")
    options.add_argument("allow-running-insecure-content")

    ua = kwargs.get("user_agent")
    if ua:
        options.add_argument(f"user-agent={ua}")

    if config["selenium"]["headless"]:
        options.add_argument("headless")
        if sys.platform in ("win32", "cygwin"):
            # fix for windows platforms
            options.add_argument("disable-gpu")

    return options


def get_config(cfg_fp="setup.cfg"):
    parser = configparser.ConfigParser()
    if not parser.read(cfg_fp):
        err = f"No such file or directory: {cfg_fp}"
        logger.error(err)
        raise EnvironmentError(err)

    valid_selenium_envs = ("local", "remote")

    # get selenium options
    env = parser.get("selenium", "env", fallback="local")
    path = parser.get("selenium", "path", fallback="chromedriver")
    url = parser.get("selenium", "url", fallback="http://127.0.0.1:4444/wd/hub")
    headless = parser.getboolean("selenium", "headless", fallback=True)

    # get automsr options
    skip = parser.get("automsr", "skip")
    # if skip was present in cfg, use it, otherwise global skips are false
    if skip:
        skip = skip.lower()
        skip_activity, skip_search = activity_skip(skip)
    else:
        skip_activity, skip_search = False, False

    retry = parser.getint("automsr", "retry", fallback=3)
    credentials = parser.get("automsr", "credentials", fallback="credentials.json")
    search_type = parser.get("automsr", "search_type", fallback="random")

    if env not in valid_selenium_envs:
        err = f"Invalid selenium env provided! Valid envs are: {valid_selenium_envs}"
        logger.error(err)
        raise ValueError(err)

    return {
        "automsr": dict(
            skip=skip,
            skip_activity=skip_activity,
            skip_search=skip_search,
            retry=retry,
            credentials=credentials,
            search_type=search_type,
        ),
        "selenium": dict(env=env, path=path, url=url, headless=headless),
    }


# read one time and then use it
config = get_config()


def get_driver(**kwargs):
    options = get_options(**kwargs)
    path = kwargs.get("path")
    url = kwargs.get("url")

    global config
    env = config["selenium"]["env"]

    if env == "local":
        path = path or config["selenium"]["path"]
        driver = Chrome(executable_path=path, options=options)
    elif env == "remote":
        url = url or config["selenium"]["url"]
        driver = Remote(
            command_executor=ChromeRemoteConnection(remote_server_addr=url),
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options,
        )
    else:
        # cannot enter this branch
        raise AssertionError

    return driver


def change_user_agent(driver, new_user_agent: str):
    # go here to check commands
    # venv/Lib/site-packages/selenium/webdriver/chrome/remote_connection.py
    cmd = "Network.setUserAgentOverride"
    cmd_args = dict(userAgent=new_user_agent)

    driver.execute("executeCdpCommand", {"cmd": cmd, "params": cmd_args})

    actual_user_agent = str(driver.execute_script("return navigator.userAgent;"))
    assert actual_user_agent == new_user_agent, "Cannot set user-agent!"
    logger.info(f"Changed user-agent to {new_user_agent}")


def test_environment(**kwargs):
    """Determine if current environment is correctly set"""
    try:
        get_driver(**kwargs).quit()
    except Exception as err:
        logger.error(str(err))
        raise err
    else:
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
            logger.error("Credentials must be object type")
            raise InvalidCredentialsError(creds_errmsg)

        email = creds.get("email")
        password = creds.get("password")
        skip = creds.get("skip")

        if not email:
            msg = f"{creds_errmsg} - Missing email"
            logger.error(msg)
            raise InvalidCredentialsError(msg)

        if not password:
            msg = f"{creds_errmsg} - Missing password"
            logger.error(msg)
            raise InvalidCredentialsError(msg)

        skip_error = (
            f"{creds_errmsg} - Invalid skip provided. "
            f"Possible values are {possible_skips}"
        )

        if not skip:
            logger.warning("Skip value missing, defaults to 'no'")
            skip = "no"

        if skip not in possible_skips:
            logger.error(skip_error)
            logger.warning("Wrong skip value, defaults to 'no'")
            skip = "no"

        creds.update(skip=skip)

        skip_activity, skip_search = activity_skip(skip)
        creds.update(skip_activity=skip_activity)
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
