import json
import unittest
from pathlib import Path

from automsr.datatypes.dashboard import Dashboard, LevelsInfoEnum

DASHBOARD_ROOT = Path(__file__).parent / "dashboards"


def load_dashboard(name: str) -> Dashboard:
    dashboards_path = DASHBOARD_ROOT
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
        self.assertIsNotNone(mobile_searches)
        assert mobile_searches is not None  # duplicate because of mypy
        self.assertEqual(len(mobile_searches), 1)
        mobile_search = mobile_searches[0]
        self.assertTrue(mobile_search.is_completable())

    def test_dashboard_not_executed(self) -> None:
        """
        Test that a dashboard with no promotion nor searches executed
        returns the expected missing completable promotions and required searches.
        """

        model = load_dashboard("no-promotions-done.json")
        promotions = model.get_completable_promotions()
        self.assertEqual(8, len(promotions))

    def test_dashboard_loading(self) -> None:
        """
        Test that all dashboards are loaded correctly.
        """

        for dashboard_file in DASHBOARD_ROOT.iterdir():
            if dashboard_file.suffix != ".json":
                continue
            _ = Dashboard(**json.load(open(dashboard_file)))
