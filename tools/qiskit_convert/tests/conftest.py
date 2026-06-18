from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILD_DIR = REPO_ROOT / "build"
BINARY = BUILD_DIR / "jeff-qiskit-convert"


def _find_qiskit_site() -> Path | None:
    """Locate the qiskit package directory."""
    try:
        import qiskit
        return Path(qiskit.__file__).parent
    except ImportError:
        pass
    candidate = (
        Path(sys.prefix)
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
        / "qiskit"
    )
    if candidate.exists():
        return candidate
    # Check common venv locations
    for p in [Path(sys.prefix) / "qiskit", Path.home() / ".local" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "qiskit"]:
        if p.exists():
            return p
    return None


def build_binary() -> Path:
    if BINARY.exists():
        return BINARY
    env = {**os.environ}
    qiskit_path = _find_qiskit_site()
    if qiskit_path:
        env["QISKIT_ROOT"] = str(qiskit_path)
    result = subprocess.run(
        ["cmake", "-B", str(BUILD_DIR), str(REPO_ROOT / "tools/qiskit_convert")],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cmake configure failed:\n{result.stdout}\n{result.stderr}")
    result = subprocess.run(
        ["cmake", "--build", str(BUILD_DIR)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cmake build failed:\n{result.stdout}\n{result.stderr}")
    return BINARY


@pytest.fixture(scope="session")
def converter() -> Path:
    return build_binary()
