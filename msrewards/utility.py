import json
import logging

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    """Error class for invalid Credentials objects"""


__possible_skips = ("no", "all", "yes", "search", "searches", "activity", "activities")


def to_skip(creds: dict):
    """Function utility to know which activity,
    listed as (daily_activities, daily_searches), is
    to be skipped.
    False means the activity should not be skipped,
    True otherwise.
    """
    if not creds.get("skip"):
        return False, False

    # lower() to ensure it's a str
    try:
        skip_str = creds["skip"].lower()
    except AttributeError:
        err = "skip value must be string!"
        logger.error(err)
        raise ValueError(err)

    if skip_str not in __possible_skips:
        err = f"skip string must be in {__possible_skips}"
        logger.error(err)
        raise ValueError(err)

    return_dict = {
        "activity": (True, False),
        "activities": (True, False),
        "search": (False, True),
        "searches": (False, True),
        "all": (True, True),
        "yes": (True, True),
        "no": (False, False),
    }
    return return_dict[skip_str]


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
        logger.error(errmsg)
        logger.error("Invalid Json provided")
        raise ValueError(errmsg)

    if not isinstance(creds_list, (list, tuple)):
        logger.error(errmsg)
        logger.error("Json must be a list of objects")
        raise ValueError(errmsg)

    for i, creds in enumerate(creds_list):
        creds_errmsg = f"{errmsg} - credentials no. {i}"
        if not isinstance(creds, dict):
            logger.error("Credentials must be object type")
            raise InvalidCredentialsError(creds_errmsg)

        email = creds.get("email")
        password = creds.get("password")
        skip = creds.get("skip")

        if any(not field for field in (email, password)):
            logger.error("Invalid email or password provided")
            raise InvalidCredentialsError(creds_errmsg)

        skip_error = f"Invalid skip provided. Possible values are {__possible_skips}"

        if not skip:
            logger.warning("Skip value missing, defaults to 'no'")
            skip = "no"

        if skip not in __possible_skips:
            logger.error(skip_error)
            logger.warning("Wrong skip value, defaults to 'no'")
            skip = "no"

        creds.update(skip=skip)

        skip_activity, skip_search = to_skip(creds)
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
