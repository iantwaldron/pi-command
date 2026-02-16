#!/usr/bin/env python3
import subprocess
import re
from pathlib import Path

from config import logger

HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")


def get_service_status(service: str) -> tuple[bool, str]:
    """Check if a service is active. Returns (is_active, status_text)."""
    result = subprocess.run(
        ["systemctl", "is-active", service],
        capture_output=True, text=True
    )
    is_active = result.stdout.strip() == "active"
    return is_active, result.stdout.strip()


def get_config_value(key: str) -> str | None:
    """Read a value from hostapd.conf."""
    try:
        result = subprocess.run(
            ["sudo", "cat", str(HOSTAPD_CONF)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            match = re.search(rf'^{key}=(.+)$', result.stdout, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def get_interface_ip(interface: str) -> str | None:
    """Get IP address of an interface."""
    result = subprocess.run(
        ["ip", "-4", "addr", "show", interface],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
        if match:
            return match.group(1)
    return None


def get_connected_clients(interface: str) -> int:
    """Get count of connected clients."""
    result = subprocess.run(
        ["iw", "dev", interface, "station", "dump"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        # Count "Station" lines
        return result.stdout.count("Station ")
    return 0


def main():
    logger.info("=== Pi Bridge Status ===\n")

    # Services
    logger.info("Services:")
    services = ["hostapd", "dnsmasq", "NetworkManager"]
    for service in services:
        active, status = get_service_status(service)
        icon = "●" if active else "○"
        logger.info(f"  {icon} {service}: {status}")

    # Check for interface-specific static IP service
    interface = get_config_value("interface") or "wlan1"
    static_service = f"{interface}-static-ip"
    active, status = get_service_status(static_service)
    icon = "●" if active else "○"
    logger.info(f"  {icon} {static_service}: {status}")

    logger.info("")

    # AP Config
    logger.info("AP Configuration:")
    ssid = get_config_value("ssid")
    country = get_config_value("country_code")
    logger.info(f"  SSID:     {ssid or 'unknown'}")
    logger.info(f"  Country:  {country or 'unknown'}")

    ip = get_interface_ip(interface)
    logger.info(f"  Interface: {interface}")
    logger.info(f"  IP:        {ip or 'not assigned'}")

    logger.info("")

    # NAT Forwarding
    logger.info("NAT Forwarding:")
    result = subprocess.run(
        ["sudo", "iptables", "-t", "nat", "-S", "POSTROUTING"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        wan_match = re.search(r'-o (\S+) -j MASQUERADE', result.stdout)
        if wan_match:
            wan_iface = wan_match.group(1)
            wan_ip = get_interface_ip(wan_iface)
            logger.info(f"  WAN interface: {wan_iface}")
            logger.info(f"  WAN IP:        {wan_ip or 'not assigned'}")
        else:
            logger.info("  No MASQUERADE rule found")
    else:
        logger.info("  Could not read iptables rules")

    logger.info("")

    # Clients
    client_count = get_connected_clients(interface)
    logger.info(f"Connected Clients: {client_count}")


if __name__ == "__main__":
    main()
