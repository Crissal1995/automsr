import logging
import random
import string
from abc import ABC
from typing import Generator

from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


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
        ...
