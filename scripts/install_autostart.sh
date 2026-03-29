#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="dash-dashboard.service"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Run as root: sudo bash scripts/install_autostart.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/src"
PYTHON3="$(command -v python3)"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

if [[ ! -f "${SRC_DIR}/main.py" ]]; then
    echo "Missing ${SRC_DIR}/main.py"
    exit 1
fi

echo "[1/4] Installing Python dependencies..."
"${PYTHON3}" -m pip install --break-system-packages -r "${SRC_DIR}/requirements.txt" 2>/dev/null || \
    "${PYTHON3}" -m pip install -r "${SRC_DIR}/requirements.txt"

echo "[2/4] Writing systemd unit: ${SERVICE_PATH}"
cat > "${SERVICE_PATH}" <<EOF
[Unit]
Description=OBD2 LED Dashboard (Python)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${SRC_DIR}
ExecStart=${PYTHON3} ${SRC_DIR}/main.py
Restart=on-failure
RestartSec=3
User=root
Group=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "[3/4] Enabling service..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "[4/4] Done."
echo "Status: systemctl status ${SERVICE_NAME} --no-pager"
echo "Logs:   journalctl -u ${SERVICE_NAME} -f"
