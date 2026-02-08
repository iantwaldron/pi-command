#!/usr/bin/env python3
import subprocess
import getpass
import re
import sys
from pathlib import Path

HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")


def read_current_config() -> dict:
    """Read current SSID from hostapd.conf."""
    config = {}
    try:
        content = HOSTAPD_CONF.read_text()
        ssid_match = re.search(r'^ssid=(.+)$', content, re.MULTILINE)
        if ssid_match:
            config["ssid"] = ssid_match.group(1)
    except PermissionError:
        # Try with sudo
        result = subprocess.run(
            ["sudo", "cat", str(HOSTAPD_CONF)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ssid_match = re.search(r'^ssid=(.+)$', result.stdout, re.MULTILINE)
            if ssid_match:
                config["ssid"] = ssid_match.group(1)
    return config


def update_config(ssid: str | None, passphrase: str | None):
    """Update hostapd.conf with new credentials."""
    # Read current config
    result = subprocess.run(
        ["sudo", "cat", str(HOSTAPD_CONF)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("Error reading hostapd.conf", file=sys.stderr)
        sys.exit(1)

    content = result.stdout

    if ssid:
        content = re.sub(r'^ssid=.+$', f'ssid={ssid}', content, flags=re.MULTILINE)

    if passphrase:
        content = re.sub(r'^wpa_passphrase=.+$', f'wpa_passphrase={passphrase}', content, flags=re.MULTILINE)

    # Write updated config
    process = subprocess.run(
        ["sudo", "tee", str(HOSTAPD_CONF)],
        input=content, text=True, capture_output=True
    )
    if process.returncode != 0:
        print("Error writing hostapd.conf", file=sys.stderr)
        sys.exit(1)


def restart_hostapd():
    """Restart hostapd service."""
    print("Restarting hostapd...")
    result = subprocess.run(["sudo", "systemctl", "restart", "hostapd"])
    if result.returncode != 0:
        print("Error restarting hostapd", file=sys.stderr)
        sys.exit(1)


def prompt(message: str, default: str | None = None) -> str:
    """Prompt for input with optional default."""
    if default:
        response = input(f"{message} [{default}]: ").strip()
        return response if response else default
    return input(f"{message}: ").strip()


def main():
    print("=== Update AP Credentials ===\n")

    current = read_current_config()
    current_ssid = current.get("ssid", "")

    print("Leave blank to keep current value.\n")

    new_ssid = input(f"New SSID [{current_ssid}]: ").strip()
    new_passphrase = getpass.getpass("New passphrase (blank to keep): ")

    if not new_ssid and not new_passphrase:
        print("No changes specified.")
        return

    # Confirm
    print("\nChanges:")
    if new_ssid:
        print(f"  SSID: {current_ssid} -> {new_ssid}")
    if new_passphrase:
        print(f"  Passphrase: (will be updated)")
    print()

    confirm = input("Apply changes? [y/N]: ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Aborted.")
        return

    print()
    update_config(new_ssid or None, new_passphrase or None)
    print("Credentials updated.")

    restart_hostapd()
    print("\nAP credentials updated successfully.")


if __name__ == "__main__":
    main()
