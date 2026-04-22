# data-analysis

Client-ready analytics workspace built around notebooks, structured datasets, and shareable HTML dashboards.

Core contents:
- `design.md` — default design system and data-visualisation guide for future dashboard/chat work
- `scripts/build_oil_dashboard.py` — fetches WTI and Brent STEO data and generates outputs
- `data/derived/oil_prices_steo.csv` — oil analysis dataset
- `dashboards/oil-prices/index.html` — interactive HTML dashboard
- `dashboards/oil-prices/data.json` — dashboard payload
- `dashboards/chat/index.html` — mobile-first chat frontend for “ask this dashboard” flows
- `backend/dashboard_chat/` — tenant-aware backend API for dashboard chat sessions
- `clients/` — per-client workspaces for separate company analyses and shareable HTML outputs
- `notebooks/oil_prices_outlook.ipynb` — supporting notebook
- `references/design-upload/` — uploaded visual reference HTML files kept as design source material

Dashboard chat backend:
- Run locally from the repo root with `python3 -m backend.dashboard_chat.server --host 127.0.0.1 --port 8765`
- Or use `scripts/run_dashboard_chat.sh` to load `/opt/data/.env` first and then start the backend
- Add `OPENAI_API_KEY` on the server when ready; until then the backend stays in grounded mock mode
- For GitHub Pages, keep the static pages on GitHub and point them at an HTTPS backend base URL hosted on your VPS
- This repo is now wired for `https://api.tasknous.com`
- Caddy deployment scaffold is in `deploy/caddy/api.tasknous.com.Caddyfile`
- Tenant manifests live under `clients/<client-name>/config/dashboards/*.json`

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
