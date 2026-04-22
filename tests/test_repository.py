import unittest
from pathlib import Path

from backend.dashboard_chat.repository import DashboardRepository, RepositoryError


class DashboardRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.repository = DashboardRepository(self.repo_root)

    def test_loads_tenant_dashboard_manifest(self):
        manifest = self.repository.load_manifest("acme-sample", "oil-prices")

        self.assertEqual(manifest["tenant_id"], "acme-sample")
        self.assertEqual(manifest["dashboard_id"], "oil-prices")
        self.assertIn("dashboard_url", manifest)
        self.assertIn("suggested_questions", manifest)
        self.assertTrue(manifest["data_path"].endswith("dashboards/oil-prices/data.json"))

    def test_rejects_unknown_dashboard(self):
        with self.assertRaises(RepositoryError):
            self.repository.load_manifest("acme-sample", "does-not-exist")


if __name__ == "__main__":
    unittest.main()
