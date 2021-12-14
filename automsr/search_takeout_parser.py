import json
import re
from pathlib import Path
from urllib.parse import urlparse


def is_valid_url(url: str):
    try:
        result = urlparse(url)
    except (AttributeError, ValueError):
        return False
    else:
        return all(field for field in (result.scheme, result.netloc, result.path))


class SearchTakeoutParser:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        with open(self.file_path) as json_file:
            self.activity = json.load(json_file)
        self.activity_count = len(self.activity)
        self._invalid_index_msg = (
            f"Invalid index, max valid is {self.activity_count - 1}"
        )

    def get_search(self, index: int):
        if index >= self.activity_count:
            raise IndexError(self._invalid_index_msg)
        return self.activity[index]

    def get_query(self, index: int):
        if index >= self.activity_count:
            raise IndexError(self._invalid_index_msg)
        title_url_query = urlparse(self.activity[index]["titleUrl"]).query.replace(
            "q=", ""
        )
        if is_valid_url(title_url_query):
            return re.sub("&usg=[a-zA-Z0-9]+", "", title_url_query)
        else:
            return title_url_query.replace("+", " ")
