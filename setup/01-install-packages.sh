#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

WIFI_CHIPSET="${WIFI_CHIPSET:-$DEFAULT_WIFI_CHIPSET}"
APT_WAIT_TIMEOUT="${APT_WAIT_TIMEOUT:-300}"
APT_WAIT_INTERVAL="${APT_WAIT_INTERVAL:-5}"

run_apt_with_lock_retry() {
    local elapsed=0

    while true; do
        if "$@"; then
            return 0
        fi

        local rc=$?
        if [ "$rc" -ne 100 ]; then
            return "$rc"
        fi

        if [ "$elapsed" -ge "$APT_WAIT_TIMEOUT" ]; then
            echo "Timed out waiting for apt lock after ${APT_WAIT_TIMEOUT}s." >&2
            return "$rc"
        fi

        echo "apt is locked by another process. Waiting ${APT_WAIT_INTERVAL}s..."
        sleep "$APT_WAIT_INTERVAL"
        elapsed=$((elapsed + APT_WAIT_INTERVAL))
    done
}

echo "Installing required packages..."
run_apt_with_lock_retry sudo apt-get update

if [ "$WIFI_CHIPSET" = "intel" ]; then
    echo "Installing Intel WiFi firmware..."
    run_apt_with_lock_retry sudo apt-get install -y firmware-iwlwifi
elif [ "$WIFI_CHIPSET" = "realtek" ]; then
    echo "Installing Realtek WiFi firmware..."
    run_apt_with_lock_retry sudo apt-get install -y firmware-realtek
else
    echo "Unknown chipset: $WIFI_CHIPSET" >&2
    exit 1
fi

echo "Installing networking packages..."
run_apt_with_lock_retry sudo apt-get install -y hostapd dnsmasq iptables-persistent

echo "Package installation complete."
