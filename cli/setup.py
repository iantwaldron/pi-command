#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import getpass
import sys
import re
from pathlib import Path

from config import logger, DEFAULTS, SETUP_DIR

STATE_FILE = Path.home() / ".cache" / "pi-bridge" / "setup-state.json"


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
        logger.warning(f"Please enter one of: {choice_str}")


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt for yes/no."""
    hint = "Y/n" if default else "y/N"
    response = input(f"{message} [{hint}]: ").strip().lower()
    if not response:
        return default
    return response in ("y", "yes")


def list_wireless_interfaces() -> list[str]:
    """Return wireless interface names discovered on the host."""
    interfaces: list[str] = []

    try:
        result = subprocess.run(
            ["iw", "dev"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                match = re.match(r"\s*Interface\s+(\S+)", line)
                if match:
                    interfaces.append(match.group(1))
    except FileNotFoundError:
        pass

    if interfaces:
        return sorted(set(interfaces))

    # Fallback: infer from interface names.
    try:
        result = subprocess.run(
            ["ip", "-o", "link", "show"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                match = re.match(r"\d+:\s*([^:]+):", line)
                if match:
                    iface = match.group(1).split("@", 1)[0]
                    if iface.startswith("wlan"):
                        interfaces.append(iface)
    except FileNotFoundError:
        pass

    return sorted(set(interfaces))


def interface_exists(interface: str) -> bool:
    """Check whether a network interface exists."""
    try:
        result = subprocess.run(
            ["ip", "link", "show", interface],
            capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def choose_default_ap_interface(config_default: str) -> str:
    """Prefer a detected wireless interface over the static default."""
    detected = list_wireless_interfaces()
    if not detected:
        return config_default

    if config_default in detected:
        return config_default

    return detected[0]


def install_packages(chipset: str):
    """Run 01-install-packages.sh"""
    if os.environ.get("PI_BRIDGE_SKIP_PACKAGE_INSTALL", "0") == "1":
        logger.info("Skipping package installation (PI_BRIDGE_SKIP_PACKAGE_INSTALL=1)")
        return

    env = os.environ.copy()
    env["WIFI_CHIPSET"] = chipset
    run_script("01-install-packages.sh", env=env)


def configure_hostapd(interface: str, ssid: str, country: str, passphrase: str):
    """Run 02-configure-hostapd.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_SSID"] = ssid
    env["AP_COUNTRY"] = country
    run_script("02-configure-hostapd.sh", env=env, stdin=passphrase + "\n")


def configure_dnsmasq(interface: str, gateway: str):
    """Run 03-configure-dnsmasq.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_GATEWAY"] = gateway
    run_script("03-configure-dnsmasq.sh", env=env)


def configure_network_manager(interface: str):
    """Run 04-configure-network-manager.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    run_script("04-configure-network-manager.sh", env=env)


def setup_nat(ap_interface: str, wan_interface: str):
    """Run 05-setup-nat.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = ap_interface
    env["WAN_INTERFACE"] = wan_interface
    run_script("05-setup-nat.sh", env=env)


def setup_service(interface: str, gateway: str):
    """Run 06-setup-service.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    env["AP_GATEWAY"] = gateway
    run_script("06-setup-service.sh", env=env)


def enable_services(interface: str):
    """Run 07-enable-services.sh"""
    env = os.environ.copy()
    env["AP_INTERFACE"] = interface
    run_script("07-enable-services.sh", env=env)


def configure_mdns():
    """Run 08-configure-mdns.sh"""
    run_script("08-configure-mdns.sh")


def load_setup_state() -> dict | None:
    """Load resumable setup state from disk."""
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def save_setup_state(config: dict):
    """Persist setup state for post-reboot resume."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "stage": "packages-installed",
        "config": config,
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2))
    os.chmod(STATE_FILE, 0o600)


def clear_setup_state():
    """Remove setup state file."""
    try:
        STATE_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def read_passphrase_from_stdin() -> str:
    """Read passphrase from stdin for non-interactive setup."""
    passphrase = sys.stdin.readline().strip()
    if not passphrase:
        logger.error("Error: passphrase required via stdin")
        sys.exit(1)
    return passphrase


def main():
    parser = argparse.ArgumentParser(description="Pi Bridge Setup")
    parser.add_argument("--use-defaults", action="store_true",
                        help="Use all defaults, read passphrase from stdin")
    args = parser.parse_args()

    logger.info("=== Pi Bridge Setup ===")

    skip_packages = os.environ.get("PI_BRIDGE_SKIP_PACKAGE_INSTALL", "0") == "1"
    state = load_setup_state()
    resuming = False

    config: dict[str, str | bool]
    if state and state.get("stage") == "packages-installed":
        cached = state.get("config", {})
        if not isinstance(cached, dict):
            cached = {}

        if args.use_defaults != bool(cached.get("use_defaults", False)):
            logger.warning("Existing setup state was created in a different mode.")
            if args.use_defaults:
                logger.warning("Re-run without --use-defaults to resume it, or delete state and start fresh.")
            else:
                logger.warning("Re-run with --use-defaults to resume it, or delete state and start fresh.")
            sys.exit(1)

        logger.info("Found previous setup state after package installation.")
        logger.info("This usually means a reboot was required to finish setup.\n")
        if args.use_defaults or prompt_yes_no("Resume setup from step 2?", default=True):
            config = cached
            resuming = True
        else:
            clear_setup_state()
            logger.info("Cleared saved setup state. Re-run setup to start over.")
            return
    else:
        if args.use_defaults:
            # Non-interactive mode - use all defaults
            config = {
                "chipset": DEFAULTS["DEFAULT_WIFI_CHIPSET"],
                "interface": choose_default_ap_interface(DEFAULTS["DEFAULT_AP_INTERFACE"]),
                "ssid": DEFAULTS["DEFAULT_AP_SSID"],
                "country": DEFAULTS["DEFAULT_AP_COUNTRY"],
                "gateway": DEFAULTS["DEFAULT_AP_GATEWAY"],
                "wan_interface": DEFAULTS["DEFAULT_WAN_INTERFACE"],
                "enable_mdns": False,
                "use_defaults": True,
            }
        else:
            # Interactive mode
            logger.info("(Press Enter to accept defaults shown in brackets)\n")

            chipset = prompt_choice("WiFi chipset", ["intel", "realtek"], default=DEFAULTS["DEFAULT_WIFI_CHIPSET"])
            default_interface = choose_default_ap_interface(DEFAULTS["DEFAULT_AP_INTERFACE"])
            interface = prompt("AP interface", default=default_interface)
            ssid = prompt("Network SSID", default=DEFAULTS["DEFAULT_AP_SSID"])

            if DEFAULTS["DEFAULT_AP_COUNTRY"] == "US":
                if prompt_yes_no("Are you in the United States?", default=True):
                    country = "US"
                else:
                    country = prompt("Country code (e.g., GB, DE, CA)").upper()
            else:
                country = prompt("Country code", default=DEFAULTS["DEFAULT_AP_COUNTRY"]).upper()

            gateway = prompt("AP gateway IP", default=DEFAULTS["DEFAULT_AP_GATEWAY"])
            wan_interface = prompt("WAN interface (internet uplink)", default=DEFAULTS["DEFAULT_WAN_INTERFACE"])
            enable_mdns = prompt_yes_no("Enable mDNS reflection (device discovery across networks)?", default=False)
            config = {
                "chipset": chipset,
                "interface": interface,
                "ssid": ssid,
                "country": country,
                "gateway": gateway,
                "wan_interface": wan_interface,
                "enable_mdns": enable_mdns,
                "use_defaults": False,
            }

    chipset = str(config["chipset"])
    interface = str(config["interface"])
    ssid = str(config["ssid"])
    country = str(config["country"])
    gateway = str(config["gateway"])
    wan_interface = str(config["wan_interface"])
    enable_mdns = bool(config["enable_mdns"])

    # Confirm
    logger.info(f"\nChipset:       {chipset}")
    logger.info(f"AP interface: {interface}")
    logger.info(f"WAN interface: {wan_interface}")
    logger.info(f"SSID:          {ssid}")
    logger.info(f"Country:       {country}")
    logger.info(f"Gateway:       {gateway}")
    logger.info(f"mDNS:          {'enabled' if enable_mdns else 'disabled'}")
    logger.info("")

    if not interface_exists(interface):
        available = list_wireless_interfaces()
        if available:
            logger.error(
                f"AP interface '{interface}' not found. Available wireless interfaces: "
                + ", ".join(available)
            )
        else:
            logger.error(
                f"AP interface '{interface}' not found. No wireless interfaces were detected."
            )
        sys.exit(1)

    if not args.use_defaults and not prompt_yes_no("Proceed with setup?", default=True):
        logger.info("Aborted.")
        return

    if not resuming:
        logger.info("")
        install_packages(chipset)
        if not skip_packages:
            save_setup_state(config)
            logger.info("")
            logger.info("Step 1 complete: packages/firmware installation finished.")
            logger.info("Reboot is required before continuing setup.")
            logger.info("After reboot, run `pi-bridge setup` again to resume from step 2.")
            return

    passphrase = read_passphrase_from_stdin() if args.use_defaults else getpass.getpass("AP passphrase: ")

    logger.info("")
    configure_hostapd(interface, ssid, country, passphrase)
    configure_dnsmasq(interface, gateway)
    configure_network_manager(interface)
    setup_nat(interface, wan_interface)
    setup_service(interface, gateway)
    enable_services(interface)
    if enable_mdns:
        configure_mdns()
    clear_setup_state()

    logger.info("\n=== Setup complete ===")


if __name__ == "__main__":
    main()
