#!/bin/bash
# Run once with: bash setup_autostart.sh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_HOME="/home/student"

echo "=== SAR Ground Station autostart setup ==="

# 1. Systemd service — starts Docker Compose on boot
sudo tee /etc/systemd/system/sar-stack.service > /dev/null << EOF
[Unit]
Description=RC SAR Ground Station Docker Compose Stack
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${PROJECT_DIR}
ExecStart=/usr/bin/docker compose -f compose.yaml -f compose.pi.yaml up -d --remove-orphans
ExecStop=/usr/bin/docker compose -f compose.yaml -f compose.pi.yaml down
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sar-stack.service
echo "[OK] systemd service enabled"

# 2. Autostart Chromium on desktop login
mkdir -p "${USER_HOME}/.config/autostart"
cat > "${USER_HOME}/.config/autostart/sar-frontend.desktop" << EOF
[Desktop Entry]
Type=Application
Name=SAR Ground Station
Comment=Open SAR frontend on startup
Exec=bash -c 'sleep 15 && chromium --noerrdialogs --disable-infobars --kiosk http://localhost:7860'
X-GNOME-Autostart-enabled=true
EOF

echo "[OK] Chromium autostart created"
echo ""
echo "Done. Reboot to test: sudo reboot"
