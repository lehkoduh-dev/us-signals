#!/usr/bin/env bash
# Забирает main из GitHub; при изменениях обновляет юниты и перезапускает сайт.
set -euo pipefail
cd "$(dirname "$0")"
git fetch -q origin main
LOCAL="$(git rev-parse HEAD)"
REMOTE="$(git rev-parse origin/main)"
[ "$LOCAL" = "$REMOTE" ] && exit 0
git reset -q --hard origin/main
bash units.sh
systemctl restart us-web.service
echo "updated ${LOCAL:0:7} -> ${REMOTE:0:7}"
