#!/bin/bash
set -e

source "$(dirname "$0")/defaults.sh"

echo "Configuring mDNS reflection..."

sudo cp /etc/avahi/avahi-daemon.conf /etc/avahi/avahi-daemon.conf.bak

# Enable reflector
sudo sed -i 's/#enable-reflector=no/enable-reflector=yes/' /etc/avahi/avahi-daemon.conf

# If the line doesn't exist, add it
if ! grep -q "enable-reflector=" /etc/avahi/avahi-daemon.conf; then
    sudo tee -a /etc/avahi/avahi-daemon.conf > /dev/null <<EOF

[reflector]
enable-reflector=yes
EOF
fi

sudo systemctl restart avahi-daemon

echo "mDNS reflection configuration complete."
