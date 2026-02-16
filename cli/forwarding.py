#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys

from config import logger, DEFAULTS

AP_INTERFACE = DEFAULTS["DEFAULT_AP_INTERFACE"]


def run_iptables(args: list[str]) -> subprocess.CompletedProcess:
    """Run an iptables command with sudo."""
    return subprocess.run(
        ["sudo", "iptables"] + args,
        capture_output=True, text=True,
    )


def rule_exists(args: list[str]) -> bool:
    """Check if an iptables rule exists using -C."""
    return run_iptables(args).returncode == 0


def list_forwarding():
    """List interfaces with NAT forwarding rules."""
    result = subprocess.run(
        ["sudo", "iptables", "-t", "nat", "-S", "POSTROUTING"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error("Could not read iptables rules")
        sys.exit(1)

    interfaces = re.findall(r'-A POSTROUTING -o (\S+) -j MASQUERADE', result.stdout)
    if not interfaces:
        logger.info("No forwarding interfaces configured.")
        return

    logger.info(f"Forwarding interfaces (AP: {AP_INTERFACE}):")
    for iface in interfaces:
        logger.info(f"  {iface}")


def nat_rules(wan_interface: str) -> list[list[str]]:
    """Return the three NAT rule arg lists for a WAN interface."""
    return [
        ["-t", "nat", "-C", "POSTROUTING", "-o", wan_interface, "-j", "MASQUERADE"],
        ["-C", "FORWARD", "-i", wan_interface, "-o", AP_INTERFACE,
         "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
        ["-C", "FORWARD", "-i", AP_INTERFACE, "-o", wan_interface, "-j", "ACCEPT"],
    ]


def add_forwarding(wan_interface: str):
    """Add NAT forwarding rules for a WAN interface."""
    rules = nat_rules(wan_interface)
    added = 0

    for check_args in rules:
        # -C checks existence; swap to -A to append
        add_args = [a if a != "-C" else "-A" for a in check_args]
        if rule_exists(check_args):
            continue
        result = run_iptables(add_args)
        if result.returncode != 0:
            logger.error(f"Failed to add rule: {result.stderr.strip()}")
            sys.exit(1)
        added += 1

    if added == 0:
        logger.info(f"Forwarding rules for {wan_interface} already exist.")
    else:
        logger.info(f"Added {added} forwarding rule(s) for {wan_interface}.")

    save_rules()


def remove_forwarding(wan_interface: str):
    """Remove NAT forwarding rules for a WAN interface."""
    rules = nat_rules(wan_interface)
    removed = 0

    for check_args in rules:
        if not rule_exists(check_args):
            continue
        # -C checks existence; swap to -D to delete
        del_args = [a if a != "-C" else "-D" for a in check_args]
        result = run_iptables(del_args)
        if result.returncode != 0:
            logger.error(f"Failed to remove rule: {result.stderr.strip()}")
            sys.exit(1)
        removed += 1

    if removed == 0:
        logger.info(f"No forwarding rules found for {wan_interface}.")
    else:
        logger.info(f"Removed {removed} forwarding rule(s) for {wan_interface}.")

    save_rules()


def save_rules():
    """Persist iptables rules with netfilter-persistent."""
    result = subprocess.run(
        ["sudo", "netfilter-persistent", "save"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error(f"Failed to save rules: {result.stderr.strip()}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Manage NAT forwarding interfaces",
    )
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("list", help="List forwarding interfaces")
    add_parser = sub.add_parser("add", help="Add forwarding for an interface")
    add_parser.add_argument("interface", help="WAN interface to forward through")
    rm_parser = sub.add_parser("remove", help="Remove forwarding for an interface")
    rm_parser.add_argument("interface", help="WAN interface to stop forwarding through")

    args = parser.parse_args()

    if args.action is None or args.action == "list":
        list_forwarding()
    elif args.action == "add":
        add_forwarding(args.interface)
    elif args.action == "remove":
        remove_forwarding(args.interface)


if __name__ == "__main__":
    main()
