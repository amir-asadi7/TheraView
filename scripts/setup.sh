#!/usr/bin/env bash

set -e

echo "======================================="
echo "      TheraView Setup Script
======================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$REPO_DIR/config/theraview.conf"
TV_PATH="$REPO_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Missing config file: $CONFIG_FILE"
    exit 1
fi

source "$CONFIG_FILE"

# Detect WiFi device
WIFI_IFACE=$(nmcli device | awk '/wifi/ {print $1}' | head -n 1)

echo "[1] Updating system..."
sudo apt update -y
sudo apt upgrade -y

echo "[2] Installing system packages..."
sudo apt install -y \
    python3 python3-pip python3-venv python3-gst-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    network-manager

echo "[3] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[4] Upgrading pip inside the venv..."
pip install --upgrade pip

echo "[5] Creating recordings directory..."
mkdir -p recordings

# ---------------------
# Systemd setup
# ---------------------
if [ "$ENABLE_SYSTEMD" = "true" ]; then
    echo "[6] Setting up systemd service..."

    SERVICE_FILE="/etc/systemd/system/theraview.service"

    sudo bash -c "cat > $SERVICE_FILE" << 'EOF'
[Unit]
Description=TheraView Capture Server
After=network.target

[Service]
ExecStart=/home/pi/TheraView/venv/bin/python3 /home/pi/TheraView/theraview.py
WorkingDirectory=/home/pi/TheraView
User=pi
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    echo "Systemd service created."
else
    echo "Systemd setup disabled by config."
fi

# ---------------------
# Hotspot setup
# ---------------------
if [ "$ENABLE_HOTSPOT" = "true" ]; then
    echo "[7] Hotspot setup enabled."

    nmcli connection delete TheraView 2>/dev/null || true

    if [ "$HOSTNAME" = "TVA" ]; then
        echo "Detected TVA. Creating hotspot TheraView."

        nmcli connection add type wifi ifname "$WIFI_IFACE" con-name TheraView autoconnect yes ssid TheraView
        nmcli connection modify TheraView wifi.mode ap
        nmcli connection modify TheraView wifi.band bg
        nmcli connection modify TheraView wifi.channel 6
        nmcli conne
