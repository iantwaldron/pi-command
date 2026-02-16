import logging
import os
from pathlib import Path

# Paths
CLI_DIR = Path(__file__).parent
PROJECT_DIR = CLI_DIR.parent
SETUP_DIR = PROJECT_DIR / "setup"

# Logging configuration
LOG_LEVEL = logging.DEBUG if os.environ.get("DEBUG", "0") == "1" else logging.INFO
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("pi-bridge")


def load_defaults() -> dict[str, str]:
    """Parse defaults.sh and return as dict."""
    defaults = {}
    defaults_file = SETUP_DIR / "defaults.sh"
    for line in defaults_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            defaults[key] = value.strip('"')
    return defaults


DEFAULTS = load_defaults()
