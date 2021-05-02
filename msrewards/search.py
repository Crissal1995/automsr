import json
import logging
import pathlib
import random
import re
import string
from abc import ABC
from typing import Generator
from urllib.parse import urlparse

from selenium.webdriver.common.keys import Keys

from msrewards.utility import config

logger = logging.getLogger(__name__)


def is_valid_url(url: str):
    try:
        result = urlparse(url)
    except (AttributeError, ValueError):
        return False
    else:
        return all(field for field in (result.scheme, result.netloc, result.path))


class SearchGenerator(ABC):
    """Interface for search generators to be used as generators of
    query for Bing searches"""

    def query_gen(self) -> Generator:
        """Returns a generator of queries to be used with Bing searches"""
        raise NotImplementedError

    @property
    def tts(self) -> float:
        """Returns the time to sleep in seconds between Bing searches"""
        raise NotImplementedError


class RandomSearchGenerator(SearchGenerator):
    @property
    def tts(self):
        return 1

    def query_gen(self):
        alphabet = string.ascii_lowercase
        length = 70
        word = "".join(random.choices(alphabet, k=length))
        logger.debug(f"Generated a word of {length} characters: {word}")

        # the first element to return is the word
        logger.debug("Yielding word...")
        yield word

        # then is always returned backspace
        while True:
            logger.debug("Yielding backspace...")
            yield Keys.BACKSPACE


class GoogleTakeoutSearchGenerator(SearchGenerator):
    @property
    def tts(self) -> float:
        return random.randint(10, 60)

    def query_gen(self) -> Generator:
        while True:
            # get a random activity from the activities
            activity = random.choice(self.activities)

            # parse query from url
            title_url_query = urlparse(activity["titleUrl"]).query.replace("q=", "")
            logger.debug(f"url query is {title_url_query}")

            # yield the correct value, based on the validity of title url query
            if is_valid_url(title_url_query):
                yield re.sub("&usg=[a-zA-Z0-9]+", "", title_url_query)
            else:
                yield title_url_query.replace("+", " ")

    def __init__(self):
        super().__init__()
        takeout_json = pathlib.Path(config["automsr"]["takeout"])
        if not takeout_json.exists():
            msg = f"Takeout json file doesn't exist! Path provided: {takeout_json}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        with open(takeout_json) as f:
            self.activities = json.load(f)

        if not self.activities:
            msg = "No activity found inside the file provided!"
            logger.error(msg)
            raise ValueError(msg)
