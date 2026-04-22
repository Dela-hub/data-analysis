import json
import unittest
from pathlib import Path

from backend.dashboard_chat.http_api import DashboardChatAPI
from backend.dashboard_chat.repository import DashboardRepository
from backend.dashboard_chat.service import ChatService


class DashboardChatAPITests(unittest.TestCase):
    def setUp(self):
        repo_root = Path(__file__).resolve().parents[1]
        self.api = DashboardChatAPI(ChatService(DashboardRepository(repo_root)))

    def test_health_check(self):
        status, headers, payload = self.api.handle_request("GET", "/api/health")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(payload["status"], "ok")

    def test_chat_roundtrip(self):
        status, _, session_payload = self.api.handle_request(
            "POST",
            "/api/chat/session",
            json.dumps(
                {
                    "tenant_id": "acme-sample",
                    "dashboard_id": "oil-prices",
                    "filters": {"series": "WTI", "range": "all", "mode": "compare"},
                }
            ).encode("utf-8"),
        )
        self.assertEqual(status, 201)

        status, _, answer_payload = self.api.handle_request(
            "POST",
            "/api/chat/ask",
            json.dumps(
                {
                    "session_id": session_payload["session_id"],
                    "question": "Summarise the near-term direction.",
                }
            ).encode("utf-8"),
        )

        self.assertEqual(status, 200)
        self.assertEqual(answer_payload["mode"], "mock")
        self.assertIn("answer", answer_payload)


if __name__ == "__main__":
    unittest.main()
