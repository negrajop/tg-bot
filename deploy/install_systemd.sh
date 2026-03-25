#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo or as root."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_WORKDIR="/opt/tg-bot"

SERVICE_NAME="${SERVICE_NAME:-tg-bot}"
APP_USER="${APP_USER:-${SUDO_USER:-root}}"
WORKDIR="${WORKDIR:-${DEFAULT_WORKDIR}}"
PYTHON_BIN="${PYTHON_BIN:-${WORKDIR}/.venv/bin/python3}"
ENV_FILE="${ENV_FILE:-${WORKDIR}/.env}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Python executable not found: ${PYTHON_BIN}"
  exit 1
fi

if [[ ! -f "${WORKDIR}/bot.py" ]]; then
  echo "bot.py not found in working directory: ${WORKDIR}"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo ".env file not found: ${ENV_FILE}"
  exit 1
fi

if [[ "${WORKDIR}" != "${PROJECT_DIR}" && ! -d "${WORKDIR}" ]]; then
  echo "Working directory not found: ${WORKDIR}"
  exit 1
fi

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=VK Mood Tracker Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${WORKDIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${PYTHON_BIN} ${WORKDIR}/bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.service"

echo "Service installed: ${SERVICE_NAME}.service"
echo "Check status with: systemctl status ${SERVICE_NAME}.service --no-pager"
