import locale
import logging
import random
import string
import sys
import warnings
from abc import ABC, abstractmethod
from typing import Generator, Optional, Set

from attr import define, field
from faker import Faker  # type: ignore
from faker.config import AVAILABLE_LOCALES as _AVAILABLE_LOCALES_IN_FAKER  # type: ignore
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger(__name__)


def _get_locale() -> str:
    """
    Workaround for `locale.getlocale()` method on Windows.

    See issues https://github.com/python/cpython/issues/82986 and
    https://github.com/pytest-dev/pytest-nunit/issues/67 to get a grasp on it.

    TL;DR: the preferred / non-deprecated-since-Py3.11 method to retrieve the current locale
    should be `locale.getlocale()`; however, on windows, the correct locale is the one
    returned from `locale.getdefaultlocale()`.
    """

    default_language_code = "en-US"

    if sys.platform not in ("win32", "cygwin"):
        language_code = locale.getlocale()[0]
        if language_code and language_code in _AVAILABLE_LOCALES_IN_FAKER:
            return language_code
        else:
            return default_language_code

    # if we are here, we need to use the workaround for Win platforms
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        language_code = locale.getdefaultlocale()[0]

    if language_code and language_code in _AVAILABLE_LOCALES_IN_FAKER:
        return language_code
    else:
        return default_language_code


def _get_faker_locales() -> Set[str]:
    return {_get_locale(), "en-US"}


@define(slots=False)
class SearchGenerator(ABC):
    """
    Interface for search generators to be used as generators of
    query for Bing searches
    """

    @abstractmethod
    def sleep_time(self) -> Generator[float, None, None]:
        """
        Returns a generator of times to wait in seconds between Bing searches,
        """

        raise NotImplementedError

    @abstractmethod
    def query(self) -> Generator[str, None, None]:
        """
        Returns a generator of queries to be used with Bing searches.
        """

        raise NotImplementedError


@define
class RandomSearchGenerator(SearchGenerator):
    def sleep_time(self) -> Generator[float, None, None]:
        while True:
            yield 1.5

    def query(self) -> Generator[str, None, None]:
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


@define
class FakerSearchGenerator(SearchGenerator):
    """
    Search Generator that uses Faker as backend for
    determining the times and the queries to use
    for Bing searches.
    """

    seed: Optional[int] = None
    _faker: Faker = field(factory=lambda: Faker(locale=list(_get_faker_locales())))

    def __attrs_post_init__(self) -> None:
        if self.seed is not None:
            self._faker.seed_instance(seed=self.seed)

    def sleep_time(self) -> Generator[float, None, None]:
        while True:
            retval: float = self._faker.pyfloat(positive=True, min_value=2, max_value=5)
            yield retval

    def query(self) -> Generator[str, None, None]:
        while True:
            sentence: str = self._faker.sentence(nb_words=6, variable_nb_words=True)

            # add manually backspaces for previous query searches
            retval = f"{Keys.BACKSPACE * 50}{sentence}"
            yield retval
