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
    :root { --bg:#071321; --panel:#0f1c31; --panel2:#132540; --line:#25466d; --text:#f4f7ff; --muted:#9fb0ca; --accent:#59a5ff; --accent2:#ffb84d; --good:#34d399; --bad:#f87171; }
    * { box-sizing:border-box; }
    body { margin:0; font-family: Inter, Arial, sans-serif; background: radial-gradient(circle at top, #14325c, #071321 58%); color:var(--text); }
    .wrap { max-width:1280px; margin:0 auto; padding:24px; }
    .hero, .controls, .cards, .grid, .story-grid { display:grid; gap:16px; }
    .hero { grid-template-columns: 1.6fr 1fr; align-items:stretch; }
    .controls { grid-template-columns: repeat(4, minmax(0,1fr)); margin:18px 0; }
    .cards { grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); margin-bottom:18px; }
    .grid { grid-template-columns: 1.7fr 1fr; }
    .story-grid { grid-template-columns: 1fr 1fr; margin-top:16px; }
    .panel { background:rgba(15,28,49,.93); border:1px solid rgba(255,255,255,.08); border-radius:22px; padding:18px; box-shadow:0 22px 50px rgba(0,0,0,.28); }
    .panel.highlight { background:linear-gradient(180deg, rgba(19,37,64,.96), rgba(10,22,38,.96)); }
    h1,h2,h3 { margin:0; }
    p { color:var(--muted); line-height:1.5; }
    label { color:var(--muted); font-size:.84rem; display:block; margin-bottom:8px; }
    select, .button { width:100%; padding:12px 14px; border-radius:14px; background:#081425; color:var(--text); border:1px solid rgba(255,255,255,.14); }
    .button { cursor:pointer; text-align:center; text-decoration:none; display:inline-block; font-weight:600; transition:.2s ease; }
    .button:hover { transform:translateY(-1px); border-color:rgba(255,255,255,.24); }
    .button.primary { background:linear-gradient(180deg,#1b4f87,#143e69); }
    .button.secondary { background:#0a1627; }
    .metric { color:var(--muted); font-size:.83rem; margin-bottom:8px; }
    .value { font-weight:800; font-size:2rem; letter-spacing:-.02em; }
    .sub { color:var(--muted); margin-top:6px; font-size:.92rem; }
    .pill-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:12px; }
    .pill { display:inline-block; padding:7px 12px; border-radius:999px; background:rgba(89,165,255,.14); color:#d6e7ff; font-size:.84rem; border:1px solid rgba(89,165,255,.2); }
    .delta.up { color:var(--good); }
    .delta.down { color:var(--bad); }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:10px 8px; border-bottom:1px solid rgba(255,255,255,.08); text-align:left; }
    th { color:var(--muted); font-size:.84rem; }
    #trendChart, #forecastChart, #spreadChart { min-height:380px; }
    .headline { font-size:1.08rem; color:var(--text); margin:8px 0 4px; }
    .story { color:var(--muted); min-height:60px; }
    .foot { color:var(--muted); font-size:.82rem; margin-top:10px; }
    @media (max-width: 1024px) { .controls, .hero, .grid, .story-grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"panel highlight\">
        <div class=\"pill\">Interactive client demo</div>
        <h1 style=\"margin-top:12px;\">Oil price outlook dashboard</h1>
        <p>This page is designed to sell the value fast: switch benchmarks, shorten the lookback window, compare Brent vs WTI, hover every chart, and export the underlying dataset. The projections shown here come directly from the official EIA Short-Term Energy Outlook.</p>
        <div class=\"pill-row\">
          <span class=\"pill\" id=\"heroRange\">Range: all data</span>
          <span class=\"pill\" id=\"heroMode\">Mode: single benchmark</span>
          <span class=\"pill\" id=\"heroUpdated\"></span>
        </div>
      </div>
      <div class=\"panel\">
        <div class=\"headline\">What a paying client immediately sees</div>
        <div class=\"story\" id=\"insightText\"></div>
        <div class=\"foot\">Use this demo flow for outreach: send the link, let the client explore, then swap sample scope for their real data and KPIs.</div>
      </div>
    </section>

    <section class=\"controls\">
      <div class=\"panel\">
        <label for=\"seriesSelect\">Primary benchmark</label>
        <select id=\"seriesSelect\"></select>
      </div>
      <div class=\"panel\">
        <label for=\"rangeSelect\">Visible history</label>
        <select id=\"rangeSelect\">
          <option value=\"12\">Last 12 months</option>
          <option value=\"24\" selected>Last 24 months</option>
          <option value=\"all\">All available months</option>
        </select>
      </div>
      <div class=\"panel\">
        <label for=\"modeSelect\">View mode</label>
        <select id=\"modeSelect\">
          <option value=\"single\" selected>Single benchmark focus</option>
          <option value=\"compare\">Compare Brent vs WTI</option>
        </select>
      </div>
      <div class=\"panel\">
        <label>Downloads</label>
        <div style=\"display:flex; gap:10px;\">
          <a class=\"button primary\" href=\"./data.json\" download>JSON</a>
          <a class=\"button secondary\" href=\"../../data/derived/oil_prices_steo.csv\" download>CSV</a>
        </div>
      </div>
    </section>

    <section class=\"cards\">
      <div class=\"panel\"><div class=\"metric\">Latest available actual</div><div class=\"value\" id=\"latestActual\">—</div><div class=\"sub\" id=\"latestActualPeriod\"></div></div>
      <div class=\"panel\"><div class=\"metric\">1-month change in actuals</div><div class=\"value\" id=\"momActual\">—</div><div class=\"sub\">Current month versus previous published month</div></div>
      <div class=\"panel\"><div class=\"metric\">3-month average projection</div><div class=\"value\" id=\"avgForecast\">—</div><div class=\"sub\">Average of the next 3 monthly forecasts</div></div>
      <div class=\"panel\"><div class=\"metric\">Projected change over 3 months</div><div class=\"value\" id=\"forecastChange\">—</div><div class=\"sub\" id=\"forecastRange\"></div></div>
    </section>

    <section class=\"grid\">
      <div class=\"panel\">
        <h3>History and forward curve</h3>
        <div id=\"trendChart\"></div>
      </div>
      <div class=\"panel\">
        <h3>Next 3 months</h3>
        <div id=\"forecastChart\"></div>
      </div>
    </section>

    <section class=\"story-grid\">
      <div class=\"panel\">
        <h3>Brent-WTI spread</h3>
        <div id=\"spreadChart\"></div>
      </div>
      <div class=\"panel\">
        <h3>Projection table</h3>
        <table>
          <thead><tr><th>Month</th><th>Projected price</th><th>Spread vs other</th></tr></thead>
          <tbody id=\"forecastTable\"></tbody>
        </table>
      </div>
    </section>
  </div>
  <script>
    const isValidNumber = value => value !== null && value !== '' && Number.isFinite(Number(value));
    const PRICE = n => `$${Math.abs(Number(n)).toFixed(2)}`;
    const PRICE_OR_DASH = n => isValidNumber(n) ? PRICE(n) : '—';
    const PRICE_SIGNED = n => isValidNumber(n) ? `${Number(n) < 0 ? '-' : '+'}${PRICE(n)}` : '—';

    async function init() {
      const payload = await fetch('./data.json').then(r => r.json());
      const summary = payload.summary;
      const rows = payload.chart_rows;
      const names = Object.keys(summary);
      const seriesSelect = document.getElementById('seriesSelect');
      const rangeSelect = document.getElementById('rangeSelect');
      const modeSelect = document.getElementById('modeSelect');
      seriesSelect.innerHTML = names.map(n => `<option value=\"${n}\">${n}</option>`).join('');
      document.getElementById('heroUpdated').textContent = `Updated: ${payload.generated_at}`;

      const bySeries = Object.fromEntries(names.map(name => [name, rows.filter(r => r.series_name === name)]));

      function getVisibleSeries(seriesRows, rangeValue) {
        if (rangeValue === 'all') return seriesRows;
        const count = Number(rangeValue);
        return seriesRows.slice(-count);
      }

      function spreadRows(rangeValue) {
        const left = getVisibleSeries(bySeries['Brent'], rangeValue);
        const right = getVisibleSeries(bySeries['WTI'], rangeValue);
        const map = new Map(right.map(r => [r.period, r]));
        return left.filter(r => map.has(r.period)).map(r => ({
          period: r.period,
          spread: +(r.value - map.get(r.period).value).toFixed(2),
          is_forecast: r.is_forecast || map.get(r.period).is_forecast,
        }));
      }

      function renderTable(primaryName, otherName) {
        const forecast = summary[primaryName].forecast_months;
        const otherMap = new Map(summary[otherName].forecast_months.map(r => [r.period, r.value]));
        document.getElementById('forecastTable').innerHTML = forecast.map(r => {
          const otherValue = otherMap.get(r.period);
          const diff = isValidNumber(r.value) && isValidNumber(otherValue) ? +(Number(r.value) - Number(otherValue)).toFixed(2) : null;
          const diffClass = diff === null ? '' : (diff >= 0 ? 'delta up' : 'delta down');
          return `<tr><td>${r.period}</td><td>${PRICE_OR_DASH(r.value)}</td><td class=\"${diffClass}\">${PRICE_SIGNED(diff)}</td></tr>`;
        }).join('');
      }

      function render(primaryName) {
        const mode = modeSelect.value;
        const rangeValue = rangeSelect.value;
        const primaryMeta = summary[primaryName];
        const otherName = names.find(n => n !== primaryName);
        const primaryRows = getVisibleSeries(bySeries[primaryName], rangeValue);
        const otherRows = getVisibleSeries(bySeries[otherName], rangeValue);
        const primaryHistory = primaryRows.filter(r => !r.is_forecast);
        const primaryForecast = primaryMeta.forecast_months;
        const spread = spreadRows(rangeValue);

        document.getElementById('latestActual').textContent = PRICE_OR_DASH(primaryMeta.latest_actual_value);
        document.getElementById('latestActualPeriod').textContent = `${primaryMeta.series_description} · ${primaryMeta.latest_actual_period}`;
        document.getElementById('momActual').textContent = PRICE_SIGNED(primaryMeta.month_over_month_actual);
        document.getElementById('avgForecast').textContent = PRICE_OR_DASH(primaryMeta.forecast_average_3m);
        document.getElementById('forecastChange').textContent = PRICE_SIGNED(primaryMeta.forecast_change_3m);
        document.getElementById('forecastRange').textContent = `${primaryMeta.forecast_start_period} to ${primaryMeta.forecast_end_period}`;
        document.getElementById('heroRange').textContent = `Range: ${rangeValue === 'all' ? 'all data' : `last ${rangeValue} months`}`;
        document.getElementById('heroMode').textContent = `Mode: ${mode === 'compare' ? 'Brent vs WTI compare' : 'single benchmark'}`;

        const spreadLatest = spread[spread.length - 1];
        const spreadText = spreadLatest && isValidNumber(spreadLatest.spread) ? PRICE_SIGNED(spreadLatest.spread) : 'unavailable';
        const story = `${primaryName} is at ${PRICE_OR_DASH(primaryMeta.latest_actual_value)} for ${primaryMeta.latest_actual_period}, with the next 3 EIA monthly points averaging ${PRICE_OR_DASH(primaryMeta.forecast_average_3m)}. Across the outlook window, ${primaryName} is projected to move ${PRICE_SIGNED(primaryMeta.forecast_change_3m)}. The current Brent-WTI spread is ${spreadText}.`;
        document.getElementById('insightText').textContent = story;

        const trendTraces = [];
        trendTraces.push({
          x: primaryRows.filter(r => !r.is_forecast).map(r => r.period),
          y: primaryRows.filter(r => !r.is_forecast).map(r => r.value),
          mode: 'lines+markers',
          type: 'scatter',
          name: `${primaryName} actual / published`,
          line: {color: '#59a5ff', width: 3},
          marker: {size: 6},
          hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
        });
        trendTraces.push({
          x: primaryForecast.map(r => r.period),
          y: primaryForecast.map(r => r.value),
          mode: 'lines+markers',
          type: 'scatter',
          name: `${primaryName} next 3 months`,
          line: {color: '#ffb84d', width: 3, dash: 'dot'},
          marker: {size: 8},
          hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
        });
        if (mode === 'compare') {
          trendTraces.push({
            x: otherRows.map(r => r.period),
            y: otherRows.map(r => r.value),
            mode: 'lines',
            type: 'scatter',
            name: `${otherName} context`,
            line: {color: '#8b9cb8', width: 2},
            hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
          });
        }
        Plotly.newPlot('trendChart', trendTraces, {
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: {l: 48, r: 12, t: 8, b: 42},
          font: {color: '#f4f7ff'},
          xaxis: {gridcolor: 'rgba(255,255,255,.08)'},
          yaxis: {title: 'USD per barrel', gridcolor: 'rgba(255,255,255,.08)'},
          legend: {orientation: 'h'}
        }, {responsive:true, displayModeBar:true, modeBarButtonsToRemove:['lasso2d','select2d']});

        const forecastCompare = new Map(summary[otherName].forecast_months.map(r => [r.period, r.value]));
        const forecastBars = [{
          x: primaryForecast.map(r => r.period),
          y: primaryForecast.map(r => r.value),
          type: 'bar',
          name: primaryName,
          marker: {color: ['#6aa8ff', '#7dcfff', '#ffb84d']},
          text: primaryForecast.map(r => PRICE(r.value)),
          textposition: 'outside',
          hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
        }];
        if (mode === 'compare') {
          forecastBars.push({
            x: summary[otherName].forecast_months.map(r => r.period),
            y: summary[otherName].forecast_months.map(r => r.value),
            type: 'bar',
            name: otherName,
            marker: {color: '#324d70'},
            hovertemplate: '%{x}<br>$%{y:.2f}/bbl<extra></extra>'
          });
        }
        Plotly.newPlot('forecastChart', forecastBars, {
          barmode: mode === 'compare' ? 'group' : 'relative',
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: {l: 44, r: 12, t: 10, b: 42},
          font: {color: '#f4f7ff'},
          xaxis: {gridcolor: 'rgba(255,255,255,.08)'},
          yaxis: {title: 'USD per barrel', gridcolor: 'rgba(255,255,255,.08)'}
        }, {responsive:true, displayModeBar:true, modeBarButtonsToRemove:['lasso2d','select2d']});

        Plotly.newPlot('spreadChart', [{
          x: spread.map(r => r.period),
          y: spread.map(r => r.spread),
          mode: 'lines+markers',
          type: 'scatter',
          fill: 'tozeroy',
          line: {color: '#b28cff', width: 3},
          marker: {size: 6},
          hovertemplate: '%{x}<br>Spread %{y:+.2f}<extra></extra>'
        }], {
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          margin: {l: 48, r: 12, t: 8, b: 42},
          font: {color: '#f4f7ff'},
          xaxis: {gridcolor: 'rgba(255,255,255,.08)'},
          yaxis: {title: 'Brent - WTI', zeroline: true, zerolinecolor: 'rgba(255,255,255,.25)', gridcolor: 'rgba(255,255,255,.08)'}
        }, {responsive:true, displayModeBar:true, modeBarButtonsToRemove:['lasso2d','select2d']});

        renderTable(primaryName, otherName);
      }

      seriesSelect.addEventListener('change', e => render(e.target.value));
      rangeSelect.addEventListener('change', () => render(seriesSelect.value));
      modeSelect.addEventListener('change', () => render(seriesSelect.value));
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
