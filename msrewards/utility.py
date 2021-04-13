import configparser
import json
import logging
import sys

from selenium.webdriver import Chrome, Remote
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Error class for invalid Credentials objects"""


def get_options(**kwargs):
    is_headless = kwargs.get("headless", True)

    options = Options()
    options.add_argument("no-sandbox")
    options.add_argument("ignore-certificate-errors")
    options.add_argument("allow-running-insecure-content")

    ua = kwargs.get("user_agent")
    if ua:
        options.add_argument(f"user-agent={ua}")

    if is_headless:
        options.add_argument("headless")
        if sys.platform in ("win32", "cygwin"):
            # fix for windows platforms
            options.add_argument("disable-gpu")

    return options


def get_driver(**kwargs):
    options = get_options(**kwargs)
    parser = configparser.ConfigParser()
    parser.read("setup.cfg")
    if not parser:
        err = "Missing or wrong setup.cfg"
        logger.error(err)
        raise EnvironmentError(err)

    valid_envs = ("local", "remote")

    env = parser.get("selenium", "env", fallback="local")
    logger.debug(f"selenium env is {env}")

    if env == "local":
        path = parser.get("selenium", "path", fallback="chromedriver")
        logger.debug(f"selenium path is {path}")
        driver = Chrome(executable_path=path, options=options)
    elif env == "remote":
        url = parser.get("selenium", "url", fallback="http://selenium-hub:4444/wd/hub")
        logger.debug(f"selenium url is {url}")
        driver = Remote(
            command_executor=url,
            desired_capabilities=DesiredCapabilities.CHROME,
            options=options,
        )
    else:
        err = f"Invalid selenium env value provided! Valid values are: {valid_envs}"
        logger.error(err)
        raise ValueError(err)

    return driver


def test_environment(**kwargs):
    """Determine if current environment is correctly set"""
    try:
        get_driver(**kwargs).quit()
    except Exception as err:
        logger.error(str(err))
        raise err
    else:
        logger.info("Selenium driver found!")


possible_skips = ("no", "all", "yes", "search", "searches", "activity", "activities")


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
        "all": (True, True),
        "no": (False, False),
    }
    skip_dict["activities"] = skip_dict["activity"]
    skip_dict["searches"] = skip_dict["search"]
    skip_dict["yes"] = skip_dict["all"]

    if any(kw not in skip_dict for kw in possible_skips):
        raise KeyError(f"Fix skip_dict! Missing some keys from {possible_skips}")

    return skip_dict[skip_str]


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
