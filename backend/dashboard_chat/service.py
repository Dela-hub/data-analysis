from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .repository import DashboardRepository, RepositoryError


@dataclass
class SessionRecord:
    session_id: str
    tenant_id: str
    dashboard_id: str
    filters: dict[str, Any]
    created_at: str
    manifest: dict[str, Any]
    payload: dict[str, Any]


class ChatService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository
        self.sessions: dict[str, SessionRecord] = {}

    def create_session(self, tenant_id: str, dashboard_id: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        manifest = self.repository.load_manifest(tenant_id, dashboard_id)
        payload = self.repository.load_dashboard_payload(tenant_id, dashboard_id)
        session_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()
        session = SessionRecord(
            session_id=session_id,
            tenant_id=tenant_id,
            dashboard_id=dashboard_id,
            filters=self._normalized_filters(filters),
            created_at=created_at,
            manifest=manifest,
            payload=payload,
        )
        self.sessions[session_id] = session
        return {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "dashboard_id": dashboard_id,
            "tenant_name": manifest.get("tenant_name", tenant_id),
            "dashboard_title": manifest.get("dashboard_title", dashboard_id),
            "dashboard_url": manifest.get("dashboard_url"),
            "created_at": created_at,
            "filters": session.filters,
            "suggested_questions": manifest.get("suggested_questions", []),
            "source_panels": manifest.get("source_panels", []),
            "refresh_label": manifest.get("refresh_label"),
        }

    def answer_question(self, session_id: str, question: str) -> dict[str, Any]:
        if not question or not question.strip():
            raise RepositoryError("Question is required")
        session = self.sessions.get(session_id)
        if session is None:
            raise RepositoryError("Unknown session")

        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            answer = self._openai_answer(session, question, openai_key)
            mode = "openai"
        else:
            answer = self._mock_answer(session, question)
            mode = "mock"

        answer.update(
            {
                "mode": mode,
                "session_id": session_id,
                "tenant_id": session.tenant_id,
                "dashboard_id": session.dashboard_id,
                "filters": session.filters,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return answer

    def get_context(self, tenant_id: str, dashboard_id: str) -> dict[str, Any]:
        manifest = self.repository.load_manifest(tenant_id, dashboard_id)
        payload = self.repository.load_dashboard_payload(tenant_id, dashboard_id)
        summary = payload.get("summary", {})
        return {
            "tenant_id": tenant_id,
            "dashboard_id": dashboard_id,
            "dashboard_title": manifest.get("dashboard_title", dashboard_id),
            "dashboard_url": manifest.get("dashboard_url"),
            "description": manifest.get("description", ""),
            "suggested_questions": manifest.get("suggested_questions", []),
            "source_panels": manifest.get("source_panels", []),
            "generated_at": payload.get("generated_at"),
            "available_series": sorted(summary.keys()),
            "summary": summary,
        }

    def _mock_answer(self, session: SessionRecord, question: str) -> dict[str, Any]:
        summary = session.payload.get("summary", {})
        filters = session.filters
        preferred_series = filters.get("series")
        if preferred_series not in summary:
            preferred_series = next(iter(summary.keys()), None)
        if preferred_series is None:
            raise RepositoryError("Dashboard summary is empty")

        series = summary[preferred_series]
        comparisons = []
        for name, item in summary.items():
            comparisons.append(
                {
                    "series": name,
                    "latest_actual_value": item.get("latest_actual_value"),
                    "forecast_change_3m": item.get("forecast_change_3m"),
                    "forecast_average_3m": item.get("forecast_average_3m"),
                }
            )
        comparisons.sort(key=lambda item: item["forecast_change_3m"])

        answer_text = (
            f"{preferred_series} moves from {series.get('latest_actual_value')} to "
            f"{series.get('forecast_end_value')} over the next three forecast points, "
            f"a {series.get('forecast_change_3m')} {series.get('unit')}. "
            f"Latest actual month: {series.get('latest_actual_period')}. "
            f"Source panels: {', '.join(session.manifest.get('source_panels', []))}."
        )

        lower_question = question.lower()
        if "compare" in lower_question or "spread" in lower_question:
            peer_bits = []
            for item in comparisons:
                peer_bits.append(
                    f"{item['series']} avg {item['forecast_average_3m']} with 3-month change {item['forecast_change_3m']}"
                )
            answer_text = (
                f"Comparison view: {'; '.join(peer_bits)}. "
                f"Source panels: {', '.join(session.manifest.get('source_panels', []))}."
            )
        elif "what changed" in lower_question or "summar" in lower_question:
            sharpest = comparisons[0]
            answer_text = (
                f"Near-term direction is softer. {preferred_series} falls from {series.get('latest_actual_value')} "
                f"to {series.get('forecast_end_value')} over three months, while the sharpest change in the dashboard "
                f"is {sharpest['series']} at {sharpest['forecast_change_3m']}. "
                f"Source panels: {', '.join(session.manifest.get('source_panels', []))}."
            )

        return {
            "answer": answer_text,
            "why_it_matters": "This keeps the discussion tied to the visible dashboard state instead of a free-form company-wide chatbot.",
            "citations": session.manifest.get("source_panels", []),
            "refresh_label": session.manifest.get("refresh_label"),
            "dashboard_generated_at": session.payload.get("generated_at"),
        }

    def _openai_answer(self, session: SessionRecord, question: str, api_key: str) -> dict[str, Any]:
        model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        system_prompt = (
            "You are answering questions about a dashboard. "
            "Use only the supplied dashboard context. "
            "If the answer is not supported by the context, say that clearly. "
            "End the main answer with 'Source panels: ...'."
        )
        user_prompt = json.dumps(
            {
                "question": question,
                "filters": session.filters,
                "manifest": {
                    "tenant_id": session.tenant_id,
                    "dashboard_id": session.dashboard_id,
                    "dashboard_title": session.manifest.get("dashboard_title"),
                    "source_panels": session.manifest.get("source_panels", []),
                    "metric_definitions": session.manifest.get("metric_definitions", {}),
                    "description": session.manifest.get("description", ""),
                },
                "summary": session.payload.get("summary", {}),
            }
        )
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        request = Request(
            url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RepositoryError(f"OpenAI request failed: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RepositoryError(f"OpenAI request failed: {exc.reason}") from exc

        message = payload["choices"][0]["message"]["content"].strip()
        return {
            "answer": message,
            "why_it_matters": "This answer was generated server-side with tenant-scoped dashboard context.",
            "citations": session.manifest.get("source_panels", []),
            "refresh_label": session.manifest.get("refresh_label"),
            "dashboard_generated_at": session.payload.get("generated_at"),
            "model": model,
        }

    @staticmethod
    def _normalized_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(filters, dict):
            return {}
        cleaned: dict[str, Any] = {}
        for key, value in filters.items():
            if value is None:
                continue
            cleaned[str(key)] = str(value)
        return cleaned
