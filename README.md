# data-analysis

Client-ready analytics workspace built around notebooks, structured datasets, and shareable HTML dashboards.

Core contents:
- `scripts/build_oil_dashboard.py` — fetches WTI and Brent STEO data and generates outputs
- `data/derived/oil_prices_steo.csv` — oil analysis dataset
- `dashboards/oil-prices/index.html` — interactive HTML dashboard
- `dashboards/oil-prices/data.json` — dashboard payload
- `notebooks/oil_prices_outlook.ipynb` — supporting notebook
- `clients/` — per-client workspaces for separate company analyses and shareable HTML outputs

Client workspace pattern:
- `clients/<client-name>/raw/`
- `clients/<client-name>/derived/`
- `clients/<client-name>/notebooks/`
- `clients/<client-name>/dashboard/`
- `clients/<client-name>/exports/`
- `clients/<client-name>/config/`

Current 3-month oil outlook generated on 2026-04-19:
- Brent: 2026-05 $112, 2026-06 $108, 2026-07 $104
- WTI: 2026-05 $99, 2026-06 $97, 2026-07 $94
