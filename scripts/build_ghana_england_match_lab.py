#!/usr/bin/env python3
"""Build the Ghana vs England Match Lab static dashboard.

Inputs:
- data/derived/ghana_england_match_lab.json

Outputs:
- dashboards/ghana-england-match-lab/index.html
- dashboards/ghana-england-match-lab/data.json
- docs/ghana-england-match-lab/index.html
- docs/ghana-england-match-lab/data.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "derived" / "ghana_england_match_lab.json"
DASHBOARD_DIR = ROOT / "dashboards" / "ghana-england-match-lab"
DOCS_DIR = ROOT / "docs" / "ghana-england-match-lab"


def build() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    embedded = {
        "ghanaPanama": payload["matches"]["ghanaPanama"],
        "englandCroatia": payload["matches"]["englandCroatia"],
    }

    # The dashboard HTML is intentionally self-contained for WhatsApp/file sharing,
    # while data.json is also published next to it for reuse/download.
    template_path = DASHBOARD_DIR / "index.html"
    html = template_path.read_text(encoding="utf-8")
    data_script = (
        '<script id="match-data" type="application/json">'
        + json.dumps(embedded, ensure_ascii=False).replace("</", "<\\/")
        + "</script>"
    )
    html = re.sub(
        r'<script id="match-data" type="application/json">.*?</script>',
        data_script,
        html,
        flags=re.S,
    )

    for out_dir in (DASHBOARD_DIR, DOCS_DIR):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        (out_dir / "data.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    build()
