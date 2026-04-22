from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .http_api import DashboardChatAPI
from .repository import DashboardRepository
from .service import ChatService


class RequestHandler(BaseHTTPRequestHandler):
    api: DashboardChatAPI

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, {}, extra_headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    def do_GET(self) -> None:  # noqa: N802
        status, headers, payload = self.api.handle_request("GET", self.path)
        self._send(status, payload, headers)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        status, headers, payload = self.api.handle_request("POST", self.path, body)
        self._send(status, payload, headers)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None, extra_headers: dict[str, str] | None = None) -> None:
        headers = headers or {}
        extra_headers = extra_headers or {}
        data = json.dumps(payload).encode("utf-8") if payload else b""
        self.send_response(status)
        for key, value in {**headers, **extra_headers}.items():
            self.send_header(key, value)
        if data:
            self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if data:
            self.wfile.write(data)


def build_api(repo_root: Path | None = None) -> DashboardChatAPI:
    repo_root = Path(repo_root or Path(__file__).resolve().parents[2]).resolve()
    repository = DashboardRepository(repo_root)
    service = ChatService(repository)
    return DashboardChatAPI(service)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tenant-aware dashboard chat backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    RequestHandler.api = build_api()
    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"dashboard-chat listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
