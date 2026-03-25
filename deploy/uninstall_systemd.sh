#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this script with sudo or as root."
  exit 1
fi

SERVICE_NAME="${SERVICE_NAME:-tg-bot}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if systemctl list-unit-files | grep -Fq "${SERVICE_NAME}.service"; then
  systemctl disable --now "${SERVICE_NAME}.service" || true
fi

if [[ -f "${SERVICE_FILE}" ]]; then
  rm -f "${SERVICE_FILE}"
fi

systemctl daemon-reload
systemctl reset-failed

echo "Service removed: ${SERVICE_NAME}.service"
