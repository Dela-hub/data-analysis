from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_ghana_england_dashboard_files_exist():
    for rel in [
        "data/derived/ghana_england_match_lab.json",
        "dashboards/ghana-england-match-lab/index.html",
        "dashboards/ghana-england-match-lab/data.json",
        "docs/ghana-england-match-lab/index.html",
        "docs/ghana-england-match-lab/data.json",
    ]:
        assert (ROOT / rel).exists(), rel


def test_ghana_england_payload_has_core_metrics():
    payload = json.loads((ROOT / "data/derived/ghana_england_match_lab.json").read_text())
    assert payload["matches"]["ghanaPanama"]["stats"]["Touches in opposition box"] == [14, 19]
    assert payload["matches"]["englandCroatia"]["stats"]["Touches in opposition box"] == [37, 16]
    assert payload["matches"]["englandCroatia"]["stats"]["Big chances"] == [7, 2]


def test_ghana_england_dashboard_no_raw_missing_tokens():
    html = (ROOT / "dashboards/ghana-england-match-lab/index.html").read_text()
    forbidden = ["NaN", "undefined", ">null<"]
    for token in forbidden:
        assert token not in html
    assert "design.md" in html
    assert "Download dashboard data" in html
    assert "match-data" in html
