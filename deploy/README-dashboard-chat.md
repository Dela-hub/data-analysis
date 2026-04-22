Dashboard chat deployment for tasknous.com

Target:
- frontend: GitHub Pages / static dashboard
- backend: https://api.tasknous.com
- backend app: 127.0.0.1:8765 on the VPS

Files prepared:
- scripts/run_dashboard_chat.sh
- deploy/caddy/api.tasknous.com.Caddyfile
- deploy/systemd/dashboard-chat.service
- dashboards/chat/config.js
- docs/chat/config.js

What the VPS still needs:
1. A process manager or startup hook to keep the backend running
2. A reverse proxy on ports 80/443 (Caddy recommended)
3. OPENAI_API_KEY in /opt/data/.env if model-backed answers are wanted

Recommended root-level commands on the VPS host:

cp /opt/data/home/workspace/data-analysis/deploy/caddy/api.tasknous.com.Caddyfile /etc/caddy/Caddyfile
chmod +x /opt/data/home/workspace/data-analysis/scripts/run_dashboard_chat.sh
caddy fmt --overwrite /etc/caddy/Caddyfile

Then run the backend wrapper under your preferred process manager.
If systemd exists on the actual VPS host, use a unit like:

[Unit]
Description=Dashboard chat backend
After=network.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/opt/data/home/workspace/data-analysis
ExecStart=/opt/data/home/workspace/data-analysis/scripts/run_dashboard_chat.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

Validation targets:
- http://127.0.0.1:8765/api/health
- https://api.tasknous.com/api/health
