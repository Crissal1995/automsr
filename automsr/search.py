import logging
import random
import string
from abc import ABC
from typing import Generator
from urllib.parse import urlparse

from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
    except (AttributeError, ValueError):
        return False
    else:
        return all(field for field in (result.scheme, result.netloc, result.path))


class SearchGenerator(ABC):
    """
    Interface for search generators to be used as generators of
    query for Bing searches
    """

    def query_gen(self) -> Generator[str, None, None]:
        """
        Returns a generator of queries to be used with Bing searches
        """

        raise NotImplementedError

    def sleep_time(self) -> float:
        """
        Returns the time to sleep in seconds between Bing searches
        """

        raise NotImplementedError


class RandomSearchGenerator(SearchGenerator):
    def sleep_time(self):
        return 1.5

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
