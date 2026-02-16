"""Tests for iptables NAT/forwarding rules."""


class TestNatRules:
    """Verify NAT rules created by setup."""

    def test_masquerade_rule(self, run):
        result = run(["iptables", "-t", "nat", "-S", "POSTROUTING"])
        assert "-o eth0 -j MASQUERADE" in result.stdout

    def test_forward_established(self, run):
        result = run(["iptables", "-S", "FORWARD"])
        assert "RELATED,ESTABLISHED" in result.stdout

    def test_forward_ap_to_wan(self, run):
        result = run(["iptables", "-S", "FORWARD"])
        assert "-i wlan1 -o eth0 -j ACCEPT" in result.stdout


class TestForwardingCli:
    """Test pi-bridge forwarding subcommand."""

    def test_forwarding_list(self, run):
        result = run(["pi-bridge", "forwarding", "list"])
        assert "eth0" in result.stdout

    def test_forwarding_add_remove(self, run):
        # Add forwarding for usb0
        run(["pi-bridge", "forwarding", "add", "usb0"])

        result = run(["iptables", "-t", "nat", "-S", "POSTROUTING"])
        assert "-o usb0 -j MASQUERADE" in result.stdout

        result = run(["iptables", "-S", "FORWARD"])
        assert "-i wlan1 -o usb0 -j ACCEPT" in result.stdout

        # Remove forwarding for usb0
        run(["pi-bridge", "forwarding", "remove", "usb0"])

        result = run(["iptables", "-t", "nat", "-S", "POSTROUTING"])
        assert "-o usb0 -j MASQUERADE" not in result.stdout

        result = run(["iptables", "-S", "FORWARD"])
        assert "-i wlan1 -o usb0 -j ACCEPT" not in result.stdout
