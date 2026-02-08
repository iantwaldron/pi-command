#!/bin/bash
set -e

AP_INTERFACE="${AP_INTERFACE:-wlan1}"
AP_SSID="${AP_SSID:-PiNet}"
AP_COUNTRY="${AP_COUNTRY:-US}"

read -r AP_PASSPHRASE

echo "Configuring hostapd..."

sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=$AP_INTERFACE
driver=nl80211
ssid=$AP_SSID
# 2.4GHz Only
hw_mode=g
channel=6
country_code=$AP_COUNTRY
ieee80211n=1
ieee80211ax=1
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$AP_PASSPHRASE
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP CCMP
rsn_pairwise=CCMP
EOF

echo "hostapd configuration complete."
