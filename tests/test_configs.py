import unittest
from pathlib import Path

from automsr.config import Config


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
        self.assertIsNotNone(config.email.sender_password)
        assert config.email.sender_password is not None  # duplicate because of mypy
        self.assertEqual(
            config.email.sender_password.get_secret_value(), "my_secret_password"
        )

    def test_non_existing_config(self) -> None:
        """
        Test that an exception is raised if a wrong value is provided to `load_config`.
        """

        with self.assertRaises(FileNotFoundError):
            load_config(name="i-do-not-exist.yaml")
