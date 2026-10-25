#!/usr/bin/env bash
# ==============================================================================
# CodeBrain Release Guardian - VM 1 Safe Provisioning & Deployment Script
# Designed for Oracle Linux 9 / OCI VM.Standard.E2.1.Micro (1.0 GB RAM / 1 OCPU)
# ==============================================================================
set -euo pipefail

APP_DIR="/home/opc/CodeBrain"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_NAME="codebrain-guardian"

echo "=== [1/6] Verifying System Resources on VM 1 ==="
TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
AVAIL_RAM_MB=$(free -m | awk '/^Mem:/{print $7}')
echo "Total RAM: ${TOTAL_RAM_MB} MB | Available RAM: ${AVAIL_RAM_MB} MB"

if [ "${TOTAL_RAM_MB}" -lt 800 ]; then
    echo "ERROR: Insufficient system memory detected."
    exit 1
fi

echo "=== [2/6] Ensuring Python 3.11 and Git are Available ==="
if ! command -v python3.11 >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
    echo "Installing python3.11, python3.11-pip, and git via DNF..."
    sudo dnf install -y --setopt=install_weak_deps=False python3.11 python3.11-pip git
fi

echo "Python 3.11 version: $(python3.11 --version)"

echo "=== [3/6] Setting Up Isolated Virtual Environment ==="
cd "${APP_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment at ${VENV_DIR}..."
    python3.11 -m venv "${VENV_DIR}"
fi

echo "=== [4/6] Installing Lean Dependencies (Throttled for 1 GB RAM) ==="
# Use nice and ionice to protect Caddy and running services from CPU/IO starvation
nice -n 15 "${VENV_DIR}/bin/pip" install --upgrade --no-cache-dir pip setuptools wheel
nice -n 15 "${VENV_DIR}/bin/pip" install --no-cache-dir -r "${APP_DIR}/deploy/requirements-lean.txt"

echo "=== [5/6] Verifying Environment Configuration ==="
if [ ! -f "${APP_DIR}/.env" ]; then
    if [ -f "${APP_DIR}/deploy/.env.vm1.template" ]; then
        echo "Creating .env from template..."
        cp "${APP_DIR}/deploy/.env.vm1.template" "${APP_DIR}/.env"
        # Generate a random DJANGO_SECRET_KEY
        SECRET_KEY=$(python3.11 -c "import secrets; print(secrets.token_urlsafe(50))")
        sed -i "s|generate-a-secure-random-string-here|${SECRET_KEY}|g" "${APP_DIR}/.env"
        echo "Generated new DJANGO_SECRET_KEY in .env."
        echo "IMPORTANT: Update .env with your FETCH_AGENT_SEED and ASI1_API_KEY!"
    else
        echo "ERROR: ${APP_DIR}/.env not found and template missing."
        exit 1
    fi
fi

chmod 600 "${APP_DIR}/.env"

echo "Running CodeBrain Release Guardian preflight check..."
"${VENV_DIR}/bin/python" -m agents.release_guardian.preflight || true

echo "=== [6/6] Installing & Starting Systemd Service ==="
sudo cp "${APP_DIR}/deploy/codebrain-guardian.service" /etc/systemd/system/${SERVICE_NAME}.service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl restart ${SERVICE_NAME}.service

echo ""
echo "=== Deployment Complete ==="
echo "Check service status with: sudo systemctl status ${SERVICE_NAME}"
echo "Check live logs with:     journalctl -u ${SERVICE_NAME} -f"
