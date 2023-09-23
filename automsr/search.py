import logging
import random
import string
from abc import ABC, abstractmethod
from typing import Generator

from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


class SearchGenerator(ABC):
    """
    Interface for search generators to be used as generators of
    query for Bing searches
    """

    @abstractmethod
    def query_gen(self) -> Generator[str, None, None]:
        """
        Returns a generator of queries to be used with Bing searches
        """

        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def sleep_time(self) -> float:
        """
        Returns the time to sleep in seconds between Bing searches
        """

        raise NotImplementedError  # pragma: no cover


class RandomSearchGenerator(SearchGenerator):
    """
    >>> search_generator = RandomSearchGenerator()
    >>> search_generator.sleep_time()
    1.5

    >>> import random
    >>> random.seed(0)
    >>> query_generator = search_generator.query_gen()
    >>> next(query_generator)
    'vtkgnkuhmpxnhtqgxzvxisxrmclpxzmwguoaskvramwgiweogzulcinycosovozpplpkoh'
    >>> for _ in range(100):
    ...     assert next(query_generator) == Keys.BACKSPACE
    """

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
