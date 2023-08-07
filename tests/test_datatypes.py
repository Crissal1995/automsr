import json
import unittest
from pathlib import Path
from typing import Dict, Any

from automsr.datatypes.dashboard import Dashboard, LevelsInfoEnum


class TestDatatypes(unittest.TestCase):
    """
    Tests collection built around datatypes.
    """

    def setUp(self) -> None:
        dashboards_path = Path(__file__).parent / "dashboards"
        self.partial_dashboard = dashboards_path / "07-08-2023.json"

    def test_dashboard(self) -> None:
        """
        Test that a valid dashboard is parsed correctly.
        """

        dashboard = self.partial_dashboard
        data: Dict[str, Any] = json.loads(dashboard.read_text())
        model = Dashboard(**data)  # validate parsing
        assert model.userStatus.levelInfo.activeLevel == LevelsInfoEnum.level_1
