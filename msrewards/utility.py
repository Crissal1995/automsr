import json
import logging

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Error class for invalid Credentials objects"""


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
