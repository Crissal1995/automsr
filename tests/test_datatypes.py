import json
import unittest
from pathlib import Path

from automsr.datatypes.dashboard import Dashboard, LevelsInfoEnum


def load_dashboard(name: str) -> Dashboard:
    dashboards_path = Path(__file__).parent / "dashboards"
    dashboard_path = dashboards_path / name
    if not dashboard_path.is_file():
        raise FileNotFoundError(dashboard_path)
    data = json.load(open(dashboard_path))
    dashboard = Dashboard(**data)
    return dashboard


class TestDatatypes(unittest.TestCase):
    """
    Tests collection built around datatypes.
    """

    def test_parsing_dashboard(self) -> None:
        """
        Test that a valid dashboard is parsed correctly.
        """

        model = load_dashboard("07-08-2023.json")
        self.assertEqual(model.userStatus.levelInfo.activeLevel, LevelsInfoEnum.LEVEL_1)

    def test_parsing_dashboard_with_mobile_searches(self) -> None:
        """
        Test that a valid dashboard at level 2 contains also mobile searches.
        """

        model = load_dashboard("08-08-2023.json")
        self.assertIsNotNone(model.userStatus.counters.mobileSearch)
        mobile_searches = model.userStatus.counters.mobileSearch
        self.assertEqual(len(mobile_searches), 1)
        mobile_search = mobile_searches[0]
        self.assertTrue(mobile_search.is_completable())
