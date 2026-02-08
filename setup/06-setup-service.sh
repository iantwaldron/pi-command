#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"
AP_GATEWAY="${AP_GATEWAY:-$DEFAULT_AP_GATEWAY}"

echo "Creating systemd service for $AP_INTERFACE..."

sudo tee /etc/systemd/system/${AP_INTERFACE}-static-ip.service > /dev/null <<EOF
[Unit]
Description=Set static IP for $AP_INTERFACE
After=network.target
Before=hostapd.service dnsmasq.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/rfkill unblock all
ExecStart=/usr/sbin/ip link set $AP_INTERFACE up
ExecStart=/usr/sbin/ip addr flush dev $AP_INTERFACE
ExecStart=/usr/sbin/ip addr add $AP_GATEWAY/24 dev $AP_INTERFACE
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${AP_INTERFACE}-static-ip.service

echo "Systemd service configuration complete."