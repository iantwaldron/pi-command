"""Tests for pi-bridge status command output."""


class TestStatusOutput:
    def test_hostapd_active(self, run):
        result = run(["pi-bridge", "status"])
        assert "hostapd: active" in result.stdout

    def test_dnsmasq_active(self, run):
        result = run(["pi-bridge", "status"])
        assert "dnsmasq: active" in result.stdout

    def test_ssid(self, run):
        result = run(["pi-bridge", "status"])
        assert "SSID:" in result.stdout
        assert "PiNet" in result.stdout

    def test_interface(self, run):
        result = run(["pi-bridge", "status"])
        assert "Interface:" in result.stdout
        assert "wlan1" in result.stdout

    def test_ip(self, run):
        result = run(["pi-bridge", "status"])
        assert "IP:" in result.stdout
        assert "192.168.31.4" in result.stdout

    def test_wan_interface(self, run):
        result = run(["pi-bridge", "status"])
        assert "WAN interface:" in result.stdout
        assert "eth0" in result.stdout
