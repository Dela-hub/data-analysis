from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class RepositoryError(RuntimeError):
    pass


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class DashboardRepository:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.clients_dir = self.repo_root / "clients"

    def list_dashboards(self) -> list[dict[str, str]]:
        manifests: list[dict[str, str]] = []
        for path in sorted(self.clients_dir.glob("*/config/dashboards/*.json")):
            data = self._read_json(path)
            manifests.append(
                {
                    "tenant_id": data["tenant_id"],
                    "tenant_name": data.get("tenant_name", data["tenant_id"]),
                    "dashboard_id": data["dashboard_id"],
                    "dashboard_title": data.get("dashboard_title", data["dashboard_id"]),
                }
            )
        return manifests

    def load_manifest(self, tenant_id: str, dashboard_id: str) -> dict[str, Any]:
        tenant_id = self._validate_slug(tenant_id, "tenant_id")
        dashboard_id = self._validate_slug(dashboard_id, "dashboard_id")
        manifest_path = self.clients_dir / tenant_id / "config" / "dashboards" / f"{dashboard_id}.json"
        if not manifest_path.exists():
            raise RepositoryError(f"Unknown dashboard '{tenant_id}/{dashboard_id}'")
        data = self._read_json(manifest_path)
        data["manifest_path"] = str(manifest_path.relative_to(self.repo_root))
        data["data_path"] = self._resolve_relative_path(data["data_path"])  # normalize before returning
        return data

    def load_dashboard_payload(self, tenant_id: str, dashboard_id: str) -> dict[str, Any]:
        manifest = self.load_manifest(tenant_id, dashboard_id)
        payload_path = self.repo_root / manifest["data_path"]
        if not payload_path.exists():
            raise RepositoryError(f"Dashboard payload missing at '{manifest['data_path']}'")
        payload = self._read_json(payload_path)
        payload["payload_path"] = manifest["data_path"]
        return payload

    def _resolve_relative_path(self, value: str) -> str:
        candidate = (self.repo_root / value).resolve()
        if self.repo_root not in candidate.parents and candidate != self.repo_root:
            raise RepositoryError(f"Refusing to read data outside repo root: {value}")
        return str(candidate.relative_to(self.repo_root))

    @staticmethod
    def _validate_slug(value: str, field_name: str) -> str:
        if not _SLUG_RE.fullmatch(value):
            raise RepositoryError(f"Invalid {field_name}: {value}")
        return value

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise RepositoryError(f"Missing JSON file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Invalid JSON in {path}") from exc
