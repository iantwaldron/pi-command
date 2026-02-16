"""Tests for interface management command."""


class TestInterfaceCommand:
    def test_show_default(self, run):
        result = run(["pi-bridge", "interface", "show"])
        assert "wlan1" in result.stdout

    def test_switch_interface(self, run):
        run(["pi-bridge", "interface", "switch", "wlan0", "--wan", "eth0"])

        result = run(["pi-bridge", "interface", "show"])
        assert "wlan0" in result.stdout

        result = run(["pi-bridge", "status"])
        assert "Interface: wlan0" in result.stdout

        # Restore default test state for subsequent tests.
        run(["pi-bridge", "interface", "switch", "wlan1", "--wan", "eth0"])

    def test_switch_wan_only(self, run):
        run(["pi-bridge", "interface", "switch", "wlan1", "--wan", "wlan0"])

        result = run(["pi-bridge", "status"])
        assert "WAN interface: wlan0" in result.stdout

        # Restore default test state for subsequent tests.
        run(["pi-bridge", "interface", "switch", "wlan1", "--wan", "eth0"])
