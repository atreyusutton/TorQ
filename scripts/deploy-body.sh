#!/usr/bin/env bash
# Copy the body code to the Pi, install dependencies, and (re)start its services.
# Usage: scripts/deploy-body.sh [ssh-host]   (default: torq)
set -euo pipefail

HOST="${1:-torq}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> syncing code to $HOST"
rsync -az --delete \
  --exclude '__pycache__' --exclude '.venv' \
  "$ROOT/body" "$ROOT/firmware" "$ROOT/config.yaml" \
  "$HOST:torq/"

echo "==> installing packages and services"
ssh "$HOST" 'bash -s' <<'REMOTE'
set -euo pipefail
cd ~/torq
if ! command -v ustreamer >/dev/null; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ustreamer
fi
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r body/requirements.txt
sudo install -m 644 body/systemd/torq-body.service body/systemd/torq-camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --quiet torq-body torq-camera
sudo systemctl restart torq-body torq-camera
sleep 2
systemctl --no-pager --lines=0 status torq-body torq-camera | grep -E '●|Active:'
REMOTE
echo "==> done. Logs: ssh $HOST journalctl -fu torq-body"
