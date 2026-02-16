#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from config import DEFAULTS, SETUP_DIR, logger

HOSTAPD_CONF = Path("/etc/hostapd/hostapd.conf")
DNSMASQ_CONF = Path("/etc/dnsmasq.conf")
NM_CONF = Path("/etc/NetworkManager/NetworkManager.conf")


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(stderr or f"Command failed: {' '.join(cmd)}")
    return result


def run_script(script_name: str, env: dict) -> None:
    script_path = SETUP_DIR / script_name
    result = subprocess.run(
        ["bash", str(script_path)],
        env=env,
        text=True,
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"{script_name} failed with exit code {result.returncode}")


def interface_exists(interface: str) -> bool:
    result = subprocess.run(
        ["ip", "link", "show", interface],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def read_file_with_sudo(path: Path) -> str:
    try:
        return path.read_text()
    except (PermissionError, FileNotFoundError):
        result = run(["sudo", "cat", str(path)], capture=True)
        return result.stdout


def write_file_with_sudo(path: Path, content: str) -> None:
    process = subprocess.run(
        ["sudo", "tee", str(path)],
        input=content,
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or f"Failed writing {path}")


def parse_hostapd_interface() -> str | None:
    content = read_file_with_sudo(HOSTAPD_CONF)
    match = re.search(r"^interface=(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_ap_gateway(ap_interface: str) -> str:
    unit_path = Path(f"/etc/systemd/system/{ap_interface}-static-ip.service")
    try:
        content = read_file_with_sudo(unit_path)
    except RuntimeError:
        return DEFAULTS["DEFAULT_AP_GATEWAY"]
    match = re.search(r"ip addr add (\d+\.\d+\.\d+\.\d+)/\d+ dev", content)
    if match:
        return match.group(1)
    return DEFAULTS["DEFAULT_AP_GATEWAY"]


def parse_wan_interface() -> str:
    result = run(["sudo", "iptables", "-t", "nat", "-S", "POSTROUTING"], capture=True)
    match = re.search(r"-A POSTROUTING -o (\S+) -j MASQUERADE", result.stdout)
    if match:
        return match.group(1)
    return DEFAULTS["DEFAULT_WAN_INTERFACE"]


def replace_line(content: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count == 0:
        if not updated.endswith("\n"):
            updated += "\n"
        updated += replacement + "\n"
    return updated


def update_interface_configs(new_interface: str) -> None:
    hostapd = read_file_with_sudo(HOSTAPD_CONF)
    hostapd = replace_line(hostapd, r"^interface=.*$", f"interface={new_interface}")
    write_file_with_sudo(HOSTAPD_CONF, hostapd)

    dnsmasq = read_file_with_sudo(DNSMASQ_CONF)
    dnsmasq = replace_line(dnsmasq, r"^interface=.*$", f"interface={new_interface}")
    write_file_with_sudo(DNSMASQ_CONF, dnsmasq)

    nm = read_file_with_sudo(NM_CONF)
    nm = replace_line(nm, r"^unmanaged-devices=.*$", f"unmanaged-devices=interface-name:{new_interface}")
    write_file_with_sudo(NM_CONF, nm)


def nat_rule_checks(ap_interface: str, wan_interface: str) -> list[list[str]]:
    return [
        ["-t", "nat", "-C", "POSTROUTING", "-o", wan_interface, "-j", "MASQUERADE"],
        ["-C", "FORWARD", "-i", wan_interface, "-o", ap_interface,
         "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
        ["-C", "FORWARD", "-i", ap_interface, "-o", wan_interface, "-j", "ACCEPT"],
    ]


def iptables_rule_exists(check_args: list[str]) -> bool:
    result = subprocess.run(
        ["sudo", "iptables"] + check_args,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def iptables_rule_add(check_args: list[str]) -> None:
    add_args = [a if a != "-C" else "-A" for a in check_args]
    run(["sudo", "iptables"] + add_args, check=True, capture=True)


def iptables_rule_del(check_args: list[str]) -> None:
    del_args = [a if a != "-C" else "-D" for a in check_args]
    run(["sudo", "iptables"] + del_args, check=True, capture=True)


def reconcile_nat_rules(old_ap: str, new_ap: str, wan: str) -> None:
    for check_args in nat_rule_checks(old_ap, wan):
        if iptables_rule_exists(check_args):
            iptables_rule_del(check_args)

    for check_args in nat_rule_checks(new_ap, wan):
        if not iptables_rule_exists(check_args):
            iptables_rule_add(check_args)

    run(["sudo", "netfilter-persistent", "save"], check=True, capture=True)


def reconcile_wan_change(ap_interface: str, old_wan: str, new_wan: str) -> None:
    for check_args in nat_rule_checks(ap_interface, old_wan):
        if iptables_rule_exists(check_args):
            iptables_rule_del(check_args)

    for check_args in nat_rule_checks(ap_interface, new_wan):
        if not iptables_rule_exists(check_args):
            iptables_rule_add(check_args)

    run(["sudo", "netfilter-persistent", "save"], check=True, capture=True)


def switch_interface(new_interface: str, wan_interface: str | None = None) -> None:
    if not interface_exists(new_interface):
        raise RuntimeError(f"Interface '{new_interface}' not found")

    old_interface = parse_hostapd_interface() or DEFAULTS["DEFAULT_AP_INTERFACE"]
    current_wan = parse_wan_interface()
    wan = wan_interface or current_wan

    if old_interface == new_interface and current_wan == wan:
        logger.info(f"AP already configured on {new_interface} with WAN {wan}.")
        return

    if old_interface == new_interface and current_wan != wan:
        logger.info(f"AP interface unchanged: {new_interface}")
        logger.info(f"Switching WAN interface: {current_wan} -> {wan}")
        logger.info("")
        reconcile_wan_change(new_interface, current_wan, wan)
        logger.info(f"WAN interface switched to {wan}.")
        return

    gateway = parse_ap_gateway(old_interface)

    logger.info(f"Switching AP interface: {old_interface} -> {new_interface}")
    logger.info(f"WAN interface: {wan}")
    logger.info("")

    update_interface_configs(new_interface)

    env = dict(os.environ)
    env["AP_INTERFACE"] = new_interface
    env["AP_GATEWAY"] = gateway
    run_script("06-setup-service.sh", env=env)

    run(["sudo", "systemctl", "disable", "--now", f"{old_interface}-static-ip.service"], check=False, capture=True)
    run(["sudo", "systemctl", "enable", f"{new_interface}-static-ip.service"], check=True, capture=True)
    run(["sudo", "systemctl", "start", f"{new_interface}-static-ip.service"], check=True, capture=True)

    reconcile_nat_rules(old_interface, new_interface, wan)

    run(["sudo", "systemctl", "restart", "NetworkManager"], check=True, capture=True)
    run(["sudo", "systemctl", "restart", "hostapd"], check=True, capture=True)
    run(["sudo", "systemctl", "restart", "dnsmasq"], check=True, capture=True)

    logger.info(f"AP interface switched to {new_interface}.")


def show_interface() -> None:
    iface = parse_hostapd_interface() or "unknown"
    logger.info(f"Configured AP interface: {iface}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage AP interface")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("show", help="Show current AP interface")

    sw = sub.add_parser("switch", help="Switch AP to a different wireless interface")
    sw.add_argument("interface", help="Interface to use as AP (e.g., wlan1)")
    sw.add_argument("--wan", help="WAN interface for NAT rules (default: current detected)")

    args = parser.parse_args()

    if args.action is None or args.action == "show":
        show_interface()
        return

    if args.action == "switch":
        switch_interface(args.interface, args.wan)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
