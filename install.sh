#!/usr/bin/env bash
# Идемпотентная установка US Market Signals (порт 8081, папка /root/us-signals).
set -euo pipefail
cd "$(dirname "$0")"
APP="$(pwd)"

apt-get install -y -qq python3-requests git >/dev/null
mkdir -p data
[ -f .env ] || { touch .env; chmod 600 .env; }

# read-only deploy key только для этого репозитория
git config core.sshCommand "ssh -i /root/.ssh/us_signals_deploy -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

# порт 8081, если включён ufw
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 8081/tcp >/dev/null
fi

bash "$APP/units.sh"
echo "Готово: http://$(hostname -I | awk '{print $1}'):8081"
