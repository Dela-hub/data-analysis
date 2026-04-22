from __future__ import annotations

import json
from typing import Any

from .repository import RepositoryError
from .service import ChatService


class DashboardChatAPI:
    def __init__(self, service: ChatService):
        self.service = service

    def handle_request(self, method: str, path: str, body: bytes | None = None) -> tuple[int, dict[str, str], dict[str, Any]]:
        body = body or b""
        try:
            if method == "GET" and path == "/api/health":
                return self._json(200, {"status": "ok"})
            if method == "GET" and path == "/api/tenants":
                return self._json(200, {"dashboards": self.service.repository.list_dashboards()})
            if method == "POST" and path == "/api/chat/session":
                payload = self._parse_json(body)
                session = self.service.create_session(
                    tenant_id=payload["tenant_id"],
                    dashboard_id=payload["dashboard_id"],
                    filters=payload.get("filters"),
                )
                return self._json(201, session)
            if method == "POST" and path == "/api/chat/ask":
                payload = self._parse_json(body)
                answer = self.service.answer_question(payload["session_id"], payload["question"])
                return self._json(200, answer)
            if method == "POST" and path == "/api/context":
                payload = self._parse_json(body)
                context = self.service.get_context(payload["tenant_id"], payload["dashboard_id"])
                return self._json(200, context)
            return self._json(404, {"error": f"Unknown route: {method} {path}"})
        except KeyError as exc:
            return self._json(400, {"error": f"Missing field: {exc.args[0]}"})
        except RepositoryError as exc:
            return self._json(400, {"error": str(exc)})
        except json.JSONDecodeError:
            return self._json(400, {"error": "Invalid JSON body"})

    @staticmethod
    def _parse_json(body: bytes) -> dict[str, Any]:
        return json.loads(body.decode("utf-8") or "{}")

    @staticmethod
    def _json(status: int, payload: dict[str, Any]) -> tuple[int, dict[str, str], dict[str, Any]]:
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        return status, headers, payload
