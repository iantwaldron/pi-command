#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"
WAN_INTERFACE="${WAN_INTERFACE:-$DEFAULT_WAN_INTERFACE}"

echo "Enabling IP forwarding..."

# Enable IP forwarding permanently
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
sudo sysctl -p

echo "Configuring iptables NAT..."

# Set up NAT masquerade
sudo iptables -t nat -A POSTROUTING -o "$WAN_INTERFACE" -j MASQUERADE
sudo iptables -A FORWARD -i "$WAN_INTERFACE" -o "$AP_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i "$AP_INTERFACE" -o "$WAN_INTERFACE" -j ACCEPT

# Save iptables rules
sudo netfilter-persistent save

echo "IP forwarding configuration complete."
