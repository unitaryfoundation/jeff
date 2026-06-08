from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILD_DIR = REPO_ROOT / "build"
BINARY = BUILD_DIR / "jeff-qiskit-convert"

QISKIT_SITE = (
    Path(sys.prefix)
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages"
    / "qiskit"
)


def build_binary() -> Path:
    if BINARY.exists():
        return BINARY
    result = subprocess.run(
        ["cmake", "-B", str(BUILD_DIR), str(REPO_ROOT / "tools/qiskit_convert")],
        capture_output=True,
        text=True,
        env={**os.environ, "QISKIT_ROOT": str(QISKIT_SITE)},
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
