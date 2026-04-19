# data-analysis

Initial oil price demo built from the U.S. EIA Short-Term Energy Outlook API.

Contents:
- `scripts/build_oil_dashboard.py` — fetches WTI and Brent STEO data and generates outputs
- `data/derived/oil_prices_steo.csv` — analysis dataset
- `dashboards/oil-prices/index.html` — interactive HTML dashboard
- `dashboards/oil-prices/data.json` — dashboard payload
- `notebooks/oil_prices_outlook.ipynb` — supporting notebook

Current 3-month outlook generated on 2026-04-19:
- Brent: 2026-05 $112, 2026-06 $108, 2026-07 $104
- WTI: 2026-05 $99, 2026-06 $97, 2026-07 $94
