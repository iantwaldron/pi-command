"""Tests that setup generated correct config files and system state."""

from pathlib import Path


class TestHostapdConf:
    conf = Path("/etc/hostapd/hostapd.conf")

    def test_exists(self):
        assert self.conf.exists()

    def test_ssid(self):
        text = self.conf.read_text()
        assert "ssid=PiNet" in text

    def test_interface(self):
        text = self.conf.read_text()
        assert "interface=wlan1" in text

    def test_passphrase(self):
        text = self.conf.read_text()
        assert "wpa_passphrase=testpassword" in text

    def test_country_code(self):
        text = self.conf.read_text()
        assert "country_code=US" in text


class TestDnsmasqConf:
    conf = Path("/etc/dnsmasq.conf")

    def test_exists(self):
        assert self.conf.exists()

    def test_interface(self):
        text = self.conf.read_text()
        assert "interface=wlan1" in text

    def test_dhcp_range(self):
        text = self.conf.read_text()
        assert "dhcp-range=192.168.31.10,192.168.31.100," in text


class TestNetworkManagerConf:
    conf = Path("/etc/NetworkManager/NetworkManager.conf")

    def test_unmanaged_device(self):
        text = self.conf.read_text()
        assert "unmanaged-devices=interface-name:wlan1" in text

    def test_dns_none(self):
        text = self.conf.read_text()
        assert "dns=none" in text


class TestSysctl:
    def test_config_file(self):
        conf = Path("/etc/sysctl.d/99-ip-forward.conf")
        assert conf.exists()
        assert "net.ipv4.ip_forward=1" in conf.read_text()

    def test_runtime_value(self, run):
        result = run(["sysctl", "-n", "net.ipv4.ip_forward"])
        assert result.stdout.strip() == "1"


class TestStaticIpService:
    service_file = Path("/etc/systemd/system/wlan1-static-ip.service")

    def test_exists(self):
        assert self.service_file.exists()

    def test_content(self):
        text = self.service_file.read_text()
        assert "192.168.31.4" in text
        assert "wlan1" in text
