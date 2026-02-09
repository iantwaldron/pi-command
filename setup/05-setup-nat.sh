#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"
WAN_INTERFACE="${WAN_INTERFACE:-$DEFAULT_WAN_INTERFACE}"

echo "Enabling IP forwarding..."

# Enable IP forwarding permanently via drop-in config
sudo tee /etc/sysctl.d/99-ip-forward.conf > /dev/null <<EOF
net.ipv4.ip_forward=1
EOF
sudo sysctl -w net.ipv4.ip_forward=1

echo "Configuring iptables NAT..."

# Set up NAT masquerade (check first to avoid duplicates)
sudo iptables -t nat -C POSTROUTING -o "$WAN_INTERFACE" -j MASQUERADE 2>/dev/null ||
  sudo iptables -t nat -A POSTROUTING -o "$WAN_INTERFACE" -j MASQUERADE
sudo iptables -C FORWARD -i "$WAN_INTERFACE" -o "$AP_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null ||
  sudo iptables -A FORWARD -i "$WAN_INTERFACE" -o "$AP_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -C FORWARD -i "$AP_INTERFACE" -o "$WAN_INTERFACE" -j ACCEPT 2>/dev/null ||
  sudo iptables -A FORWARD -i "$AP_INTERFACE" -o "$WAN_INTERFACE" -j ACCEPT

# Save iptables rules
sudo netfilter-persistent save

echo "IP forwarding configuration complete."
