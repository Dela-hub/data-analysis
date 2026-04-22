from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_oil_dashboard.py"
SPEC = importlib.util.spec_from_file_location("build_oil_dashboard", MODULE_PATH)
build_oil_dashboard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_oil_dashboard)


class BuildOilDashboardTests(unittest.TestCase):
    def test_write_dashboard_updates_docs_publish_copy(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "period": pd.Timestamp("2026-04-01"),
                    "series_name": "Brent",
                    "value": 124.0,
                    "is_forecast": False,
                },
                {
                    "period": pd.Timestamp("2026-05-01"),
                    "series_name": "Brent",
                    "value": 112.0,
                    "is_forecast": True,
                },
            ]
        )
        summary = {
            "Brent": {
                "series_name": "Brent",
                "series_description": "Brent spot price",
                "unit": "USD",
                "latest_actual_period": "2026-04",
                "latest_actual_value": 124.0,
                "month_over_month_actual": 5.0,
                "forecast_start_period": "2026-05",
                "forecast_start_value": 112.0,
                "forecast_end_period": "2026-07",
                "forecast_end_value": 104.0,
                "forecast_average_3m": 108.0,
                "forecast_change_3m": -20.0,
                "forecast_months": [
                    {"period": "2026-05", "value": 112.0},
                    {"period": "2026-06", "value": 108.0},
                    {"period": "2026-07", "value": 104.0},
                ],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            dash_dir = repo / "dashboards" / "oil-prices"
            docs_dir = repo / "docs" / "oil-prices"
            with patch.object(build_oil_dashboard, "REPO", repo), patch.object(build_oil_dashboard, "DASH_DIR", dash_dir), patch.object(build_oil_dashboard, "DOCS_DASH_DIR", docs_dir):
                build_oil_dashboard.write_dashboard(df, summary)

            dash_payload = json.loads((dash_dir / "data.json").read_text())
            docs_payload = json.loads((docs_dir / "data.json").read_text())

            self.assertEqual(docs_payload, dash_payload)
            self.assertEqual((docs_dir / "index.html").read_text(), (dash_dir / "index.html").read_text())

    def test_write_dashboard_keeps_full_history_but_only_three_forecast_months(self) -> None:
        df = pd.DataFrame(
            [
                {"period": pd.Timestamp("2026-03-01"), "series_name": "Brent", "value": 103.13, "is_forecast": False},
                {"period": pd.Timestamp("2026-04-01"), "series_name": "Brent", "value": 124.0, "is_forecast": False},
                {"period": pd.Timestamp("2026-05-01"), "series_name": "Brent", "value": 112.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-06-01"), "series_name": "Brent", "value": 108.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-07-01"), "series_name": "Brent", "value": 104.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-08-01"), "series_name": "Brent", "value": 99.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-03-01"), "series_name": "WTI", "value": 91.38, "is_forecast": False},
                {"period": pd.Timestamp("2026-04-01"), "series_name": "WTI", "value": 109.0, "is_forecast": False},
                {"period": pd.Timestamp("2026-05-01"), "series_name": "WTI", "value": 99.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-06-01"), "series_name": "WTI", "value": 97.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-07-01"), "series_name": "WTI", "value": 94.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-08-01"), "series_name": "WTI", "value": 90.0, "is_forecast": True},
            ]
        )
        summary = {
            "Brent": {
                "series_name": "Brent",
                "series_description": "Brent spot price",
                "unit": "USD",
                "latest_actual_period": "2026-04",
                "latest_actual_value": 124.0,
                "month_over_month_actual": 20.87,
                "forecast_start_period": "2026-05",
                "forecast_start_value": 112.0,
                "forecast_end_period": "2026-07",
                "forecast_end_value": 104.0,
                "forecast_average_3m": 108.0,
                "forecast_change_3m": -20.0,
                "forecast_months": [
                    {"period": "2026-05", "value": 112.0},
                    {"period": "2026-06", "value": 108.0},
                    {"period": "2026-07", "value": 104.0},
                ],
            },
            "WTI": {
                "series_name": "WTI",
                "series_description": "WTI spot price",
                "unit": "USD",
                "latest_actual_period": "2026-04",
                "latest_actual_value": 109.0,
                "month_over_month_actual": 17.62,
                "forecast_start_period": "2026-05",
                "forecast_start_value": 99.0,
                "forecast_end_period": "2026-07",
                "forecast_end_value": 94.0,
                "forecast_average_3m": 96.67,
                "forecast_change_3m": -15.0,
                "forecast_months": [
                    {"period": "2026-05", "value": 99.0},
                    {"period": "2026-06", "value": 97.0},
                    {"period": "2026-07", "value": 94.0},
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            dash_dir = repo / "dashboards" / "oil-prices"
            docs_dir = repo / "docs" / "oil-prices"
            with patch.object(build_oil_dashboard, "REPO", repo), patch.object(build_oil_dashboard, "DASH_DIR", dash_dir), patch.object(build_oil_dashboard, "DOCS_DASH_DIR", docs_dir):
                build_oil_dashboard.write_dashboard(df, summary)
            payload = json.loads((dash_dir / "data.json").read_text())

        periods = sorted({row["period"] for row in payload["chart_rows"]})
        self.assertEqual(periods, ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07"])


if __name__ == "__main__":
    unittest.main()
