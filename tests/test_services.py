"""Tests that services are in the correct state after setup."""


class TestServiceActive:
    """All core services should be active after setup."""

    def test_hostapd_active(self, run):
        result = run(["systemctl", "is-active", "hostapd"])
        assert result.stdout.strip() == "active"

    def test_dnsmasq_active(self, run):
        result = run(["systemctl", "is-active", "dnsmasq"])
        assert result.stdout.strip() == "active"

    def test_network_manager_active(self, run):
        result = run(["systemctl", "is-active", "NetworkManager"])
        assert result.stdout.strip() == "active"

    def test_static_ip_active(self, run):
        result = run(["systemctl", "is-active", "wlan1-static-ip"])
        assert result.stdout.strip() == "active"


class TestServiceEnabled:
    """Key services should be enabled to start on boot."""

    def test_hostapd_enabled(self, run):
        result = run(["systemctl", "is-enabled", "hostapd"])
        assert result.stdout.strip() == "enabled"

    def test_dnsmasq_enabled(self, run):
        result = run(["systemctl", "is-enabled", "dnsmasq"])
        assert result.stdout.strip() == "enabled"


class TestStopStart:
    """pi-bridge stop/start should toggle service state."""

    def test_stop_and_start(self, run):
        # Stop AP
        run(["pi-bridge", "stop"])

        result = run(
            ["systemctl", "is-active", "hostapd"], check=False
        )
        assert result.stdout.strip() == "inactive"

        result = run(
            ["systemctl", "is-active", "dnsmasq"], check=False
        )
        assert result.stdout.strip() == "inactive"

        # Start AP back up
        run(["pi-bridge", "start"])

        result = run(["systemctl", "is-active", "hostapd"])
        assert result.stdout.strip() == "active"

        result = run(["systemctl", "is-active", "dnsmasq"])
        assert result.stdout.strip() == "active"
