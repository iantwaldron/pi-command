#!/bin/bash
set -e

WIFI_CHIPSET="${WIFI_CHIPSET:-intel}"

echo "Installing required packages..."
sudo apt update

if [ "$WIFI_CHIPSET" = "intel" ]; then
    echo "Installing Intel WiFi firmware..."
    sudo apt install -y firmware-iwlwifi
elif [ "$WIFI_CHIPSET" = "realtek" ]; then
    echo "Installing Realtek WiFi firmware..."
    sudo apt install -y firmware-realtek
else
    echo "Unknown chipset: $WIFI_CHIPSET" >&2
    exit 1
fi

echo "Installing networking packages..."
sudo apt install -y hostapd dnsmasq iptables-persistent
