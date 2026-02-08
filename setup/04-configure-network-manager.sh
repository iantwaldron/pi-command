#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"

echo "Configuring NetworkManager..."

# Backup existing config
sudo cp /etc/NetworkManager/NetworkManager.conf /etc/NetworkManager/NetworkManager.conf.bak

# Update config
sudo tee /etc/NetworkManager/NetworkManager.conf > /dev/null <<EOF
[main]
plugins=ifupdown,keyfile
dns=none

[ifupdown]
managed=false

[keyfile]
unmanaged-devices=interface-name:$AP_INTERFACE
EOF

echo "NetworkManager configuration complete."