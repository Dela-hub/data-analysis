# Client workspace structure

Use one folder per company under `clients/`.

Recommended layout:

- `clients/<client-name>/raw/` — original source files
- `clients/<client-name>/derived/` — cleaned / transformed datasets
- `clients/<client-name>/notebooks/` — analysis notebooks
- `clients/<client-name>/dashboard/` — final HTML dashboard and payloads
- `clients/<client-name>/dashboard/assets/` — dashboard images, logos, QR assets
- `clients/<client-name>/exports/` — packaged deliverables, CSV extracts, zips
- `clients/<client-name>/config/` — client-specific config or metadata

Rules:
- Keep each client isolated inside their own folder.
- Put shareable HTML pages inside `dashboard/`.
- Reuse shared scripts where possible, but do not mix client raw data.
- Use lowercase kebab-case for client folder names.

Example share paths on GitHub Pages once published through `docs/`:
- `/clients/acme/dashboard/`
- `/clients/nova-energy/dashboard/`

Template:
- `clients/_template/` contains the base folder structure for new client work.
