#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"

echo "Enabling and starting services..."

# Enable services
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Ensure wifi radios are unblocked
sudo rfkill unblock wifi
sudo nmcli radio wifi on

# Restart NetworkManager first
sudo systemctl restart NetworkManager
sleep 2

# Start AP interface IP service
sudo systemctl start ${AP_INTERFACE}-static-ip.service

# Start hostapd
sudo systemctl restart hostapd

# Start dnsmasq
sudo systemctl restart dnsmasq

echo ""
echo "Service Status:"
sudo systemctl status ${AP_INTERFACE}-static-ip.service --no-pager | head -5
sudo systemctl status hostapd --no-pager | head -5
sudo systemctl status dnsmasq --no-pager | head -5

echo "Services configuration complete."
