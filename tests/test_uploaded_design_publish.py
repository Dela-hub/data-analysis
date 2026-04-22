from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BUILD_MODULE_PATH = REPO / "scripts" / "build_oil_dashboard.py"
SPEC = importlib.util.spec_from_file_location("build_oil_dashboard", BUILD_MODULE_PATH)
build_oil_dashboard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(build_oil_dashboard)


class UploadedDesignPublishTests(unittest.TestCase):
    def test_generated_dashboard_uses_uploaded_design_markers(self) -> None:
        df = pd.DataFrame(
            [
                {"period": pd.Timestamp("2026-04-01"), "series_name": "Brent", "value": 124.0, "is_forecast": False},
                {"period": pd.Timestamp("2026-05-01"), "series_name": "Brent", "value": 112.0, "is_forecast": True},
                {"period": pd.Timestamp("2026-04-01"), "series_name": "WTI", "value": 109.0, "is_forecast": False},
                {"period": pd.Timestamp("2026-05-01"), "series_name": "WTI", "value": 99.0, "is_forecast": True},
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

        build_oil_dashboard.write_dashboard(df, summary)
        html = (REPO / "dashboards" / "oil-prices" / "index.html").read_text()

        self.assertIn("DM Sans", html)
        self.assertIn("Chart.js", html)
        self.assertIn("Prices peaked in April", html)
        self.assertIn("dela<span>.</span>", html)
        self.assertNotIn("Oil market intelligence", html)
        self.assertNotIn("Plotly.newPlot", html)

    def test_chat_publish_uses_uploaded_shell_and_backend_api(self) -> None:
        html = (REPO / "docs" / "chat" / "index.html").read_text()

        self.assertIn("DM Sans", html)
        self.assertIn("dela<span>.</span>", html)
        self.assertIn("Ask the data", html)
        self.assertIn("/api/chat/ask", html)
        self.assertIn("/api/chat/session", html)
        self.assertNotIn("window.claude.complete", html)


if __name__ == "__main__":
    unittest.main()
