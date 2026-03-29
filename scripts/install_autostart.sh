#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="dash-dashboard.service"
DEVICE_PATH="${1:-/dev/ttyUSB0}"

if [[ "${EUID}" -ne 0 ]]; then
    echo "Uruchom jako root: sudo bash scripts/install_autostart.sh [/dev/ttyUSB0]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_PATH="${REPO_ROOT}/core/dashboard_app"
WORK_DIR="${REPO_ROOT}/core"
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}"

echo "[1/4] Budowanie aplikacji..."
make -C "${REPO_ROOT}"

if [[ ! -x "${APP_PATH}" ]]; then
    echo "Nie znaleziono pliku wykonywalnego: ${APP_PATH}"
    exit 1
fi

echo "[2/4] Tworzenie uslugi systemd: ${SERVICE_PATH}"
cat > "${SERVICE_PATH}" <<EOF
[Unit]
Description=OBD2 LED Dashboard
After=multi-user.target dev-ttyUSB0.device
Wants=dev-ttyUSB0.device

[Service]
Type=simple
WorkingDirectory=${WORK_DIR}
ExecStart=${APP_PATH} --device ${DEVICE_PATH}
Restart=always
RestartSec=2
User=root
Group=root
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "[3/4] Aktywacja uslugi..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo "[4/4] Gotowe."
echo "Status: systemctl status ${SERVICE_NAME} --no-pager"
echo "Logi:   journalctl -u ${SERVICE_NAME} -f"
