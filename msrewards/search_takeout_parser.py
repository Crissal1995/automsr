import json
import re
from pathlib import Path
from urllib.parse import urlparse


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except Exception:
        return False


class SearchTakeoutParser:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        with open(self.file_path) as json_file:
            self.activity = json.load(json_file)
        self.n_of_search = len(self.activity)

    def get_search(self, indices: int):
        if indices < self.n_of_search:
            return self.activity[indices]
        else:
            raise IndexError("Indice non valido")

    def get_query(self, indices: int):
        if indices < self.n_of_search:
            title_url_query = urlparse(
                self.activity[indices]["titleUrl"]
            ).query.replace("q=", "")
            if is_valid_url(title_url_query):
                return re.sub("&usg=[a-zA-Z0-9]+", "", title_url_query)
            else:
                return title_url_query.replace("+", " ")
        else:
            raise IndexError("Indice non valido")


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    parser = SearchTakeoutParser("./LeMieAttività.json")
    print(parser.get_query(3))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
