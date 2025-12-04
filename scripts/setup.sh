#!/usr/bin/env bash

set -e

echo "======================================="
echo "      TheraView Setup Script
======================================="

TV_PATH="$(pwd)"
HOSTNAME="$(hostname)"
CONFIG_FILE="config/theraview.conf"

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
SERVICE_FILE="/etc/systemd/system/theraview.service"

if [ "$ENABLE_SYSTEMD" = "true" ]; then
    echo "[6] Creating systemd service..."

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

    sudo systemctl daemon-reload
    sudo systemctl enable theraview.service
    sudo systemctl restart theraview.service

    echo "Systemd service active."

else
    echo "[6] Systemd disabled. Checking for existing service..."

    if [ -f "$SERVICE_FILE" ]; then
        echo "Service found. Removing it."
        sudo systemctl stop theraview.service 2>/dev/null || true
        sudo systemctl disable theraview.service 2>/dev/null || true
        sudo rm -f "$SERVICE_FILE"
        sudo systemctl daemon-reload
        echo "Systemd service removed."
    else
        echo "No service found."
    fi
fi


# ---------------------
# Hotspot setup
# ---------------------
THERA_NET="TheraView"
PRECONFIGURED_NET="preconfigured"

if [ "$ENABLE_HOTSPOT" = "true" ]; then
    echo "[7] Hotspot enabled."

    nmcli device wifi rescan

    if [ "$HOSTNAME" = "TVA" ]; then
        echo "TVA detected. Creating hotspot."

        nmcli connection delete "$THERA_NET" 2>/dev/null || true

        nmcli connection add type wifi ifname "$WIFI_IFACE" \
            con-name "$THERA_NET" autoconnect yes ssid "$THERA_NET"

        nmcli connection modify "$THERA_NET" wifi.mode ap
        nmcli connection modify "$THERA_NET" wifi.band bg
        nmcli connection modify "$THERA_NET" wifi.channel 6
        nmcli connection modify "$THERA_NET" wifi-sec.key-mgmt wpa-psk
        nmcli connection modify "$THERA_NET" wifi-sec.psk "ritaengs"
        nmcli connection modify "$THERA_NET" ipv4.method shared

        nmcli connection up "$THERA_NET"

    elif [ "$HOSTNAME" = "TVB" ]; then
        echo "TVB detected. Connecting to hotspot."

        nmcli device wifi rescan

        if nmcli device wifi list | grep -q "$THERA_NET"; then
            nmcli connection delete "$THERA_NET" 2>/dev/null || true

            nmcli connection add type wifi ifname "$WIFI_IFACE" \
                con-name "$THERA_NET" ssid "$THERA_NET" \
                wifi-sec.key-mgmt wpa-psk wifi-sec.psk "ritaengs" autoconnect yes

            nmcli connection up "$THERA_NET" || true
        else
            echo "Hotspot not visible. Waiting for TVA to broadcast."
        fi

    else
        echo "Hostname not TVA or TVB. Skipping hotspot steps."
    fi

else
    echo "[7] Hotspot disabled. Removing hotspot profiles if present."

    if nmcli connection show | grep -q "$THERA_NET"; then
        echo "Removing TheraView connection."
        nmcli connection delete "$THERA_NET" 2>/dev/null || true
    fi

    nmcli device wifi rescan

    if nmcli device wifi list | grep -q "$PRECONFIGURED_NET"; then
        echo "Preconfigured network found. Connecting."
        nmcli connection up "$PRECONFIGURED_NET" || true
    else
        echo "Preconfigured network not found."
    fi
fi


echo ""
echo "======================================="
echo "      TheraView setup complete"
echo "======================================="
