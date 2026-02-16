FROM debian:bookworm

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pytest \
    python3-pytest-cov \
    sudo \
    bash \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Root runs sudo commands in scripts without prompts.
RUN echo 'root ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/root-nopasswd

# Files/directories expected by setup scripts when package install is skipped.
RUN mkdir -p /etc/hostapd /etc/NetworkManager /etc/systemd/system /etc/sysctl.d /var/lib/misc && \
    touch /etc/NetworkManager/NetworkManager.conf

# Lightweight command shims used by tests to model service/network behavior
# without requiring systemd as PID 1 or privileged containers.
COPY stubs/ /usr/local/bin/
RUN chmod +x /usr/local/bin/systemctl /usr/local/bin/iptables \
    /usr/local/bin/rfkill /usr/local/bin/nmcli /usr/local/bin/netfilter-persistent \
    /usr/local/bin/iw /usr/local/bin/journalctl /usr/local/bin/sysctl /usr/local/bin/ip

WORKDIR /opt/pi-bridge
ENV PATH="/opt/pi-bridge/bin:/usr/local/bin:${PATH}"

CMD ["bash"]
