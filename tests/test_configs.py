import json
import unittest
from pathlib import Path

import yaml

from automsr.datatypes.dashboard import Dashboard, LevelsInfoEnum
from config import Config


def load_config(name: str) -> Config:
    configs_path = Path(__file__).parent / "configs"
    config_path = configs_path / name
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    config = Config.from_yaml(config_path)
    return config


class TestConfigs(unittest.TestCase):
    """
    Tests collection built around config model.
    """

    def test_parsing_config(self) -> None:
        """
        Test that a valid config is parsed correctly.
        """

        config = load_config("config.example.yaml")
        self.assertEqual(len(config.automsr.profiles), 1)
        self.assertEqual(config.version, "v1")
        self.assertEqual(config.email.sender_password.get_secret_value(), "my_secret_password")
