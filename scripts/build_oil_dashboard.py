#!/opt/data/pyenv/bin/python
from __future__ import annotations

import json
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
NOTEBOOK_DIR = REPO / "notebooks"


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

        summary[series_name] = {
            "series_name": series_name,
            "series_description": latest_actual["seriesDescription"],
            "unit": latest_actual["unit"],
            "latest_actual_period": latest_actual["period"].strftime("%Y-%m"),
            "latest_actual_value": round(float(latest_actual["value"]), 2),
            "forecast_start_period": first_forecast["period"].strftime("%Y-%m"),
            "forecast_start_value": round(float(first_forecast["value"]), 2),
            "forecast_end_period": last_forecast["period"].strftime("%Y-%m"),
            "forecast_end_value": round(float(last_forecast["value"]), 2),
            "forecast_average_3m": round(float(forecast["value"].mean()), 2),
            "forecast_change_3m": round(float(last_forecast["value"] - latest_actual["value"]), 2),
            "forecast_months": [
                {"period": row["period"].strftime("%Y-%m"), "value": round(float(row["value"]), 2)}
                for _, row in forecast.iterrows()
            ],
        }
    return summary


def write_dashboard(df: pd.DataFrame, summary: dict) -> None:
    DASH_DIR.mkdir(parents=True, exist_ok=True)
    chart_rows = []
    for _, row in df.iterrows():
        chart_rows.append(
            {
                "period": row["period"].strftime("%Y-%m"),
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

    html = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Oil Price Outlook</title>
  <script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>
  <style>
    :root { --bg:#06111f; --panel:#0d1b2f; --line:#214164; --text:#f3f6ff; --muted:#9fb0ca; --accent:#4da3ff; --accent2:#ffb84d; }
    * { box-sizing:border-box; }
    body { margin:0; font-family: Inter, Arial, sans-serif; background: radial-gradient(circle at top, #10233f, #06111f 60%); color:var(--text); }
    .wrap { max-width:1240px; margin:0 auto; padding:24px; }
    .hero, .cards, .grid { display:grid; gap:16px; }
    .hero { grid-template-columns: 2fr 1fr; align-items:stretch; }
    .cards { grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); margin:18px 0; }
    .grid { grid-template-columns: 2fr 1fr; }
    .panel { background:rgba(13,27,47,.92); border:1px solid rgba(255,255,255,.08); border-radius:18px; padding:18px; box-shadow:0 18px 50px rgba(0,0,0,.25); }
    h1,h2,h3 { margin:0; }
    p { color:var(--muted); }
    label { color:var(--muted); font-size:.88rem; display:block; margin-bottom:8px; }
    select { width:100%; padding:12px; border-radius:12px; background:#081425; color:var(--text); border:1px solid rgba(255,255,255,.14); }
    .metric { color:var(--muted); font-size:.85rem; margin-bottom:8px; }
    .value { font-weight:700; font-size:1.9rem; }
    .sub { color:var(--muted); margin-top:6px; font-size:.92rem; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:10px 8px; border-bottom:1px solid rgba(255,255,255,.08); text-align:left; }
    th { color:var(--muted); font-size:.84rem; }
    #trendChart, #forecastChart { min-height:360px; }
    .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(77,163,255,.14); color:#cfe3ff; font-size:.84rem; }
    @media (max-width: 900px) { .hero, .grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"panel\">
        <div class=\"pill\">Interactive client demo</div>
        <h1 style=\"margin-top:12px;\">Oil price outlook dashboard</h1>
        <p>This dashboard uses official U.S. EIA Short-Term Energy Outlook monthly series and highlights the next 3 months for WTI and Brent. It is designed as a polished HTML client preview with mobile-friendly interaction.</p>
      </div>
      <div class=\"panel\">
        <label for=\"seriesSelect\">Oil benchmark</label>
        <select id=\"seriesSelect\"></select>
        <div class=\"sub\" id=\"seriesDesc\" style=\"margin-top:12px;\"></div>
        <div class=\"sub\" id=\"generatedAt\" style=\"margin-top:10px;\"></div>
      </div>
    </section>

    <section class=\"cards\">
      <div class=\"panel\"><div class=\"metric\">Latest available actual</div><div class=\"value\" id=\"latestActual\">—</div><div class=\"sub\" id=\"latestActualPeriod\"></div></div>
      <div class=\"panel\"><div class=\"metric\">3-month average projection</div><div class=\"value\" id=\"avgForecast\">—</div><div class=\"sub\">Average of the next 3 monthly forecasts</div></div>
      <div class=\"panel\"><div class=\"metric\">Projected change over 3 months</div><div class=\"value\" id=\"forecastChange\">—</div><div class=\"sub\" id=\"forecastRange\"></div></div>
    </section>

    <section class=\"grid\">
      <div class=\"panel\">
        <h3>History + forecast</h3>
        <div id=\"trendChart\"></div>
      </div>
      <div class=\"panel\">
        <h3>Next 3 months</h3>
        <div id=\"forecastChart\"></div>
      </div>
    </section>

    <section class=\"panel\" style=\"margin-top:16px;\">
      <h3 style=\"margin-bottom:12px;\">Projection table</h3>
      <table>
        <thead><tr><th>Month</th><th>Projected price</th></tr></thead>
        <tbody id=\"forecastTable\"></tbody>
      </table>
    </section>
  </div>
  <script>
    const PRICE = n => `$${Math.abs(n).toFixed(2)}`;
    const PRICE_SIGNED = n => `${n < 0 ? '-' : '+'}${PRICE(n)}`;
    async function init() {
      const payload = await fetch('./data.json').then(r => r.json());
      const summary = payload.summary;
      const rows = payload.chart_rows;
      const names = Object.keys(summary);
      const select = document.getElementById('seriesSelect');
      select.innerHTML = names.map(n => `<option value=\"${n}\">${n}</option>`).join('');
      document.getElementById('generatedAt').textContent = `Generated from EIA STEO data on ${payload.generated_at}`;

      function render(name) {
        const meta = summary[name];
        const seriesRows = rows.filter(r => r.series_name === name);
        const history = seriesRows.filter(r => !r.is_forecast);
        const forecast = meta.forecast_months;

        document.getElementById('seriesDesc').textContent = meta.series_description;
        document.getElementById('latestActual').textContent = PRICE(meta.latest_actual_value);
        document.getElementById('latestActualPeriod').textContent = `Period: ${meta.latest_actual_period}`;
        document.getElementById('avgForecast').textContent = PRICE(meta.forecast_average_3m);
        document.getElementById('forecastChange').textContent = PRICE_SIGNED(meta.forecast_change_3m);
        document.getElementById('forecastRange').textContent = `${meta.forecast_start_period} to ${meta.forecast_end_period}`;
        document.getElementById('forecastTable').innerHTML = forecast.map(r => `<tr><td>${r.period}</td><td>${PRICE(r.value)}</td></tr>`).join('');

        Plotly.newPlot('trendChart', [
          {
            x: history.map(r => r.period),
            y: history.map(r => r.value),
            mode: 'lines+markers',
            type: 'scatter',
            name: 'Actual / published',
            line: {color: '#4da3ff', width: 3},
            marker: {size: 6},
            hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
          },
          {
            x: forecast.map(r => r.period),
            y: forecast.map(r => r.value),
            mode: 'lines+markers',
            type: 'scatter',
            name: 'Next 3 months',
            line: {color: '#ffb84d', width: 3, dash: 'dot'},
            marker: {size: 7},
            hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
          }
        ], {
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: {l: 48, r: 12, t: 8, b: 42},
          font: {color: '#f3f6ff'},
          xaxis: {gridcolor: 'rgba(255,255,255,.08)'},
          yaxis: {title: 'USD per barrel', gridcolor: 'rgba(255,255,255,.08)'},
          legend: {orientation: 'h'}
        }, {responsive:true, displayModeBar:false});

        Plotly.newPlot('forecastChart', [{
          x: forecast.map(r => r.period),
          y: forecast.map(r => r.value),
          type: 'bar',
          marker: {color: ['#6aa8ff', '#7dcfff', '#ffb84d']},
          text: forecast.map(r => PRICE(r.value)),
          textposition: 'outside',
          hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
        }], {
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: {l: 44, r: 12, t: 10, b: 42},
          font: {color: '#f3f6ff'},
          xaxis: {gridcolor: 'rgba(255,255,255,.08)'},
          yaxis: {title: 'USD per barrel', gridcolor: 'rgba(255,255,255,.08)'}
        }, {responsive:true, displayModeBar:false});
      }

      select.addEventListener('change', e => render(e.target.value));
      render(names[0]);
    }
    init();
  </script>
</body>
</html>
"""
    (DASH_DIR / "index.html").write_text(html)


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
