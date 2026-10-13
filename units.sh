#!/usr/bin/env bash
# Идемпотентно создаёт systemd-юниты us-web и us-update (автообновление раз в 5 минут).
set -euo pipefail
APP="$(cd "$(dirname "$0")" && pwd)"
SD=/etc/systemd/system

cat > $SD/us-web.service <<EOF
[Unit]
Description=US Market Signals web
After=network-online.target

[Service]
WorkingDirectory=$APP
EnvironmentFile=-$APP/.env
Environment=PORT=8081
ExecStart=/usr/bin/python3 $APP/web.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

cat > $SD/us-update.service <<EOF
[Unit]
Description=US Market Signals git pull
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$APP
ExecStart=/bin/bash $APP/update.sh
EOF

cat > $SD/us-update.timer <<EOF
[Unit]
Description=US Market Signals auto-update every 5 min

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min
Unit=us-update.service

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now us-web.service us-update.timer >/dev/null
