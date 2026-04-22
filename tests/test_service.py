import unittest
from pathlib import Path

from backend.dashboard_chat.repository import DashboardRepository
from backend.dashboard_chat.service import ChatService


class ChatServiceTests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]
        self.service = ChatService(DashboardRepository(self.repo_root))

    def test_creates_tenant_bound_session(self):
        session = self.service.create_session(
            tenant_id="acme-sample",
            dashboard_id="oil-prices",
            filters={"series": "Brent", "range": "24", "mode": "single"},
        )

        self.assertEqual(session["tenant_id"], "acme-sample")
        self.assertEqual(session["dashboard_id"], "oil-prices")
        self.assertIn("session_id", session)
        self.assertIn("suggested_questions", session)
        self.assertEqual(session["filters"]["series"], "Brent")

    def test_answers_with_grounded_mock_response_when_openai_key_is_missing(self):
        session = self.service.create_session(
            tenant_id="acme-sample",
            dashboard_id="oil-prices",
            filters={"series": "Brent", "range": "24", "mode": "single"},
        )

        answer = self.service.answer_question(session["session_id"], "What changes next over the next three months?")

        self.assertEqual(answer["mode"], "mock")
        self.assertEqual(answer["tenant_id"], "acme-sample")
        self.assertEqual(answer["dashboard_id"], "oil-prices")
        self.assertIn("Source panels", answer["answer"])
        self.assertIn("Brent", answer["answer"])
        self.assertTrue(answer["citations"])


if __name__ == "__main__":
    unittest.main()
