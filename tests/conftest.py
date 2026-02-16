import os
import subprocess

import pytest


@pytest.fixture
def run():
    """Helper that calls subprocess.run with common defaults.

    Merges stderr into stdout so callers can just check result.stdout
    regardless of whether the command uses logging (stderr) or print (stdout).
    """

    def _run(cmd, **kwargs):
        kwargs.setdefault("stderr", subprocess.STDOUT)
        kwargs.setdefault("check", True)
        kwargs.setdefault("text", True)
        return subprocess.run(cmd, stdout=subprocess.PIPE, **kwargs)

    return _run


@pytest.fixture(scope="session", autouse=True)
def setup_ap():
    """Run pi-bridge setup once before all tests."""
    env = dict(os.environ)
    env["PI_BRIDGE_SKIP_PACKAGE_INSTALL"] = "1"

    subprocess.run(
        ["pi-bridge", "setup", "--use-defaults"],
        input="testpassword\n",
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
