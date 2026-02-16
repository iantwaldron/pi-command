# Docker Dev/Test Environment

A minimal Debian Bookworm container used for both local development (IDE interpreter) and CI test execution.

It intentionally avoids full `systemd`-in-container setup. Instead, tests run against lightweight command stubs (`systemctl`, `iptables`, `nmcli`, `rfkill`, etc.) so you can validate script/CLI behavior without PID 1 and privileged Docker complexity.

## Quick Start

```bash
cd docker
docker compose up -d --build dev
docker exec -it pi-bridge-dev bash
```

Inside container:

```bash
pi-bridge --help
pytest tests -v
```

## Run Tests

```bash
cd docker
docker compose run --rm test
```

## IDE Interpreter

Use the same image as your interpreter runtime:

1. Build with `docker compose build dev`
2. Point IDE to container `pi-bridge-dev`
3. Use `/usr/bin/python3` inside the container

## Notes

- Project is mounted at `/opt/pi-bridge`.
- Test stubs live in `docker/stubs/` and shadow system commands in `/usr/local/bin`.
- This setup is for behavior verification of your scripts/CLI, not hardware-level Wi-Fi validation.
