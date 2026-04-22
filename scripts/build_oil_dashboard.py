#!/opt/data/pyenv/bin/python
from __future__ import annotations

import json
import math
import os
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import nbformat
import pandas as pd
from dateutil.relativedelta import relativedelta

BASE_URL = "https://api.eia.gov/v2/steo/data/"
SERIES = {
    "WTIPUUS": "WTI",
    "BREPUUS": "Brent",
}
REPO = Path(__file__).resolve().parents[1]
DATA_DIR = REPO / "data" / "derived"
DASH_DIR = REPO / "dashboards" / "oil-prices"
DOCS_DASH_DIR = REPO / "docs" / "oil-prices"
NOTEBOOK_DIR = REPO / "notebooks"
TEMPLATE_PATH = REPO / "templates" / "oil-dashboard-template.html"


def fetch_series(series_id: str) -> list[dict]:
    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        raise RuntimeError("EIA_API_KEY is not set")
    params = [
        ("api_key", api_key),
        ("frequency", "monthly"),
        ("data[0]", "value"),
        ("facets[seriesId][]", series_id),
        ("start", "2024-01"),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", "0"),
        ("length", "5000"),
    ]
    url = f"{BASE_URL}?{urlencode(params)}"
    with urlopen(url, timeout=60) as response:
        payload = json.load(response)
    return payload["response"]["data"]


def build_dataset() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for series_id, short_name in SERIES.items():
        rows = fetch_series(series_id)
        frame = pd.DataFrame(rows)
        frame["series_name"] = short_name
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"])
    df = df[["period", "seriesId", "series_name", "seriesDescription", "unit", "value"]]
    df = df.sort_values(["series_name", "period"]).reset_index(drop=True)

    current_month = pd.Timestamp(date.today().replace(day=1))
    df["is_forecast"] = df["period"] > current_month
    return df


def safe_number(value: float | int | None) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        return None
    return round(value, 2)


def build_summary(df: pd.DataFrame) -> dict:
    current_month = pd.Timestamp(date.today().replace(day=1))
    target_months = [current_month + relativedelta(months=i) for i in range(1, 4)]
    summary: dict[str, dict] = {}

    for series_name in sorted(df["series_name"].unique()):
        subset = df[df["series_name"] == series_name].sort_values("period")
        history = subset[subset["period"] <= current_month]
        forecast = subset[subset["period"].isin(target_months)]
        if history.empty or forecast.empty:
            raise RuntimeError(f"Missing history or forecast rows for {series_name}")

        latest_actual = history.iloc[-1]
        first_forecast = forecast.iloc[0]
        last_forecast = forecast.iloc[-1]
        prev_actual = history.iloc[-2] if len(history) > 1 else latest_actual
        summary[series_name] = {
            "series_name": series_name,
            "series_description": latest_actual["seriesDescription"],
            "unit": latest_actual["unit"],
            "latest_actual_period": latest_actual["period"].strftime("%Y-%m"),
            "latest_actual_value": safe_number(latest_actual["value"]),
            "month_over_month_actual": safe_number(latest_actual["value"] - prev_actual["value"]),
            "forecast_start_period": first_forecast["period"].strftime("%Y-%m"),
            "forecast_start_value": safe_number(first_forecast["value"]),
            "forecast_end_period": last_forecast["period"].strftime("%Y-%m"),
            "forecast_end_value": safe_number(last_forecast["value"]),
            "forecast_average_3m": safe_number(forecast["value"].mean()),
            "forecast_change_3m": safe_number(last_forecast["value"] - latest_actual["value"]),
            "forecast_months": [
                {"period": row["period"].strftime("%Y-%m"), "value": safe_number(row["value"])}
                for _, row in forecast.iterrows()
            ],
        }
    return summary


def build_dashboard_html() -> str:
    return TEMPLATE_PATH.read_text()


def sync_dashboard_publish_copy() -> None:
    DOCS_DASH_DIR.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "data.json"):
        (DOCS_DASH_DIR / filename).write_text((DASH_DIR / filename).read_text())


def write_dashboard(df: pd.DataFrame, summary: dict) -> None:
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    allowed_forecast_periods = {
        month["period"]
        for item in summary.values()
        for month in item.get("forecast_months", [])
    }
    chart_rows = []
    for _, row in df.iterrows():
        period = row["period"].strftime("%Y-%m")
        if bool(row["is_forecast"]) and period not in allowed_forecast_periods:
            continue
        chart_rows.append(
            {
                "period": period,
                "series_name": row["series_name"],
                "value": round(float(row["value"]), 2),
                "is_forecast": bool(row["is_forecast"]),
            }
        )

    data_payload = {
        "generated_at": date.today().isoformat(),
        "summary": summary,
        "chart_rows": chart_rows,
    }
    (DASH_DIR / "data.json").write_text(json.dumps(data_payload, indent=2))
    (DASH_DIR / "index.html").write_text(build_dashboard_html())
    sync_dashboard_publish_copy()


def write_notebook() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_markdown_cell(
            "# Oil prices outlook\n\n"
            "This notebook documents the EIA Short-Term Energy Outlook pull used for the interactive dashboard.\n\n"
            "Series included:\n"
            "- WTI (`WTIPUUS`)\n"
            "- Brent (`BREPUUS`)\n"
        ),
        nbformat.v4.new_code_cell(
            "import json\n"
            "from pathlib import Path\n"
            "import pandas as pd\n\n"
            "root = Path.cwd()\n"
            "df = pd.read_csv(root / 'data' / 'derived' / 'oil_prices_steo.csv')\n"
            "summary = json.loads((root / 'dashboards' / 'oil-prices' / 'data.json').read_text())['summary']\n"
            "df.head()"
        ),
        nbformat.v4.new_code_cell(
            "df.groupby('series_name').tail(6)[['period','series_name','value','is_forecast']]"
        ),
        nbformat.v4.new_code_cell(
            "pd.DataFrame([\n"
            "    {\n"
            "        'series': k,\n"
            "        'latest_actual': v['latest_actual_value'],\n"
            "        'mom_actual': v['month_over_month_actual'],\n"
            "        'forecast_average_3m': v['forecast_average_3m'],\n"
            "        'forecast_change_3m': v['forecast_change_3m']\n"
            "    } for k, v in summary.items()\n"
            "])"
        ),
    ]
    (NOTEBOOK_DIR / "oil_prices_outlook.ipynb").write_text(nbformat.writes(nb))


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = build_dataset()
    csv_path = DATA_DIR / "oil_prices_steo.csv"
    df.assign(period=df["period"].dt.strftime("%Y-%m")).to_csv(csv_path, index=False)
    summary = build_summary(df)
    write_dashboard(df, summary)
    write_notebook()
    print(f"saved_csv={csv_path.relative_to(REPO)}")
    print(f"saved_dashboard={DASH_DIR.relative_to(REPO) / 'index.html'}")
    print(f"saved_notebook={NOTEBOOK_DIR.relative_to(REPO) / 'oil_prices_outlook.ipynb'}")
    for name, values in summary.items():
        months = ", ".join(f"{m['period']}: ${m['value']:.2f}" for m in values['forecast_months'])
        print(f"{name} next 3 months -> {months}")


if __name__ == "__main__":
    main()
