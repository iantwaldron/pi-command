#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

AP_INTERFACE="${AP_INTERFACE:-$DEFAULT_AP_INTERFACE}"
AP_GATEWAY="${AP_GATEWAY:-$DEFAULT_AP_GATEWAY}"

# Derive subnet prefix from gateway (strip last octet)
SUBNET_PREFIX="${AP_GATEWAY%.*}"

echo "Configuring dnsmasq..."

sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
bind-interfaces
no-ping
interface=$AP_INTERFACE
dhcp-range=${SUBNET_PREFIX}.10,${SUBNET_PREFIX}.100,255.255.255.0,24h
dhcp-option=3,$AP_GATEWAY
dhcp-option=6,8.8.8.8,8.8.4.4
EOF

echo "dnsmasq configuration complete."