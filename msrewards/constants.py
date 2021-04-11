import abc
import string


# config class to provide utility methods
class Config(abc.ABC):
    @classmethod
    def get_config(cls):
        raise NotImplementedError


class SearchConfig(Config):
    search_config = {
        "max_mobile": 20,
        "max_desktop": 30,
        "max_word_length": 70,
        "offset": 10,
        "alphabet": string.ascii_lowercase,
    }

    @classmethod
    def get_config(cls):
        return cls.search_config
