#!/usr/bin/env python3
import argparse
import subprocess
import getpass
import sys
from pathlib import Path

SETUP_DIR = Path(__file__).parent.parent / "setup"


def load_defaults() -> dict[str, str]:
    """Parse defaults.sh and return as dict."""
    defaults = {}
    defaults_file = SETUP_DIR / "defaults.sh"
    for line in defaults_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            defaults[key] = value.strip('"')
    return defaults


DEFAULTS = load_defaults()


def run_script(script_name: str, env: dict | None = None, stdin: str | None = None):
    """Run a setup script with optional env vars and stdin."""
    script_path = SETUP_DIR / script_name
    result = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        input=stdin,
        text=True,
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


def prompt(message: str, default: str | None = None) -> str:
    """Prompt for input with optional default."""
    if default:
        response = input(f"{message} [{default}]: ").strip()
        return response if response else default
    return input(f"{message}: ").strip()


def prompt_choice(message: str, choices: list[str], default: str | None = None) -> str:
    """Prompt for a choice from a list."""
    choice_str = "/".join(choices)
    if default:
        response = input(f"{message} ({choice_str}) [{default}]: ").strip().lower()
        return response if response else default
    while True:
        response = input(f"{message} ({choice_str}): ").strip().lower()
        if response in choices:
            return response
        print(f"Please enter one of: {choice_str}")


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt for yes/no."""
    hint = "Y/n" if default else "y/N"
    response = input(f"{message} [{hint}]: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def install_packages(chipset: str):
    """Run 01-install-packages.sh"""
    import os
    env = os.environ.copy()
    env["WIFI_CHIPSET"] = chipset
    run_script("01-install-packages.sh", env=env)


def configure_hostapd(interface: str, ssid: str, country: str, passphrase: str):
    """Run 02-configure-hostapd.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_SSID"] = ssid
    env["AP_COUNTRY"] = country
    run_script("02-configure-hostapd.sh", env=env, stdin=passphrase)


def configure_dnsmasq(interface: str, gateway: str):
    """Run 03-configure-dnsmasq.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_GATEWAY"] = gateway
    run_script("03-configure-dnsmasq.sh", env=env)


def configure_network_manager(interface: str):
    """Run 04-configure-network-manager.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    run_script("04-configure-network-manager.sh", env=env)


def setup_nat(ap_interface: str, wan_interface: str):
    """Run 05-setup-nat.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = ap_interface
    env["WAN_INTERFACE"] = wan_interface
    run_script("05-setup-nat.sh", env=env)


def setup_service(interface: str, gateway: str):
    """Run 06-setup-service.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_GATEWAY"] = gateway
    run_script("06-setup-service.sh", env=env)


def enable_services(interface: str):
    """Run 07-enable-services.sh"""
    import os
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    run_script("07-enable-services.sh", env=env)


def configure_mdns():
    """Run 08-configure-mdns.sh"""
    run_script("08-configure-mdns.sh")


def main():
    parser = argparse.ArgumentParser(description="Pi Command Setup")
    parser.add_argument("--use-defaults", action="store_true",
                        help="Use all defaults, read passphrase from stdin")
    args = parser.parse_args()

    print("=== Pi Command Setup ===")

    if args.use_defaults:
        # Non-interactive mode - use all defaults
        chipset = DEFAULTS["DEFAULT_WIFI_CHIPSET"]
        interface = DEFAULTS["DEFAULT_AP_INTERFACE"]
        ssid = DEFAULTS["DEFAULT_AP_SSID"]
        country = DEFAULTS["DEFAULT_AP_COUNTRY"]
        gateway = DEFAULTS["DEFAULT_AP_GATEWAY"]
        wan_interface = DEFAULTS["DEFAULT_WAN_INTERFACE"]
        enable_mdns = False
        passphrase = sys.stdin.readline().strip()
        if not passphrase:
            print("Error: passphrase required via stdin", file=sys.stderr)
            sys.exit(1)
    else:
        # Interactive mode
        print("(Press Enter to accept defaults shown in brackets)\n")

        chipset = prompt_choice("WiFi chipset", ["intel", "realtek"], default=DEFAULTS["DEFAULT_WIFI_CHIPSET"])
        interface = prompt("AP interface", default=DEFAULTS["DEFAULT_AP_INTERFACE"])
        ssid = prompt("Network SSID", default=DEFAULTS["DEFAULT_AP_SSID"])

        if DEFAULTS["DEFAULT_AP_COUNTRY"] == "US":
            if prompt_yes_no("Are you in the United States?", default=True):
                country = "US"
            else:
                country = prompt("Country code (e.g., GB, DE, CA)").upper()
        else:
            country = prompt("Country code", default=DEFAULTS["DEFAULT_AP_COUNTRY"]).upper()

        passphrase = getpass.getpass("AP passphrase: ")

        gateway = prompt("AP gateway IP", default=DEFAULTS["DEFAULT_AP_GATEWAY"])
        wan_interface = prompt("WAN interface (internet uplink)", default=DEFAULTS["DEFAULT_WAN_INTERFACE"])
        enable_mdns = prompt_yes_no("Enable mDNS reflection (device discovery across networks)?", default=False)

    # Confirm
    print(f"\nChipset:      {chipset}")
    print(f"AP interface: {interface}")
    print(f"WAN interface: {wan_interface}")
    print(f"SSID:         {ssid}")
    print(f"Country:      {country}")
    print(f"Gateway:      {gateway}")
    print(f"mDNS:         {'enabled' if enable_mdns else 'disabled'}")
    print()

    if not args.use_defaults and not prompt_yes_no("Proceed with setup?", default=True):
        print("Aborted.")
        return

    print()
    install_packages(chipset)
    configure_hostapd(interface, ssid, country, passphrase)
    configure_dnsmasq(interface, gateway)
    configure_network_manager(interface)
    setup_nat(interface, wan_interface)
    setup_service(interface, gateway)
    enable_services(interface)
    if enable_mdns:
        configure_mdns()

    print("\n=== Setup complete ===")


if __name__ == "__main__":
    main()
