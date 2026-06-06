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
    Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages" / "qiskit"
)

try:
    import qiskit  # noqa: F401
except ImportError:
    pytest.skip("Qiskit is not installed — skipping qiskit_convert tests", allow_module_level=True)


def _build_binary() -> Path:
    if BINARY.exists():
        return BINARY
    result = subprocess.run(
        ["cmake", "-B", str(BUILD_DIR), str(REPO_ROOT / "tools/qiskit_convert")],
        capture_output=True, text=True,
        env={**os.environ, "QISKIT_ROOT": str(QISKIT_SITE)},
    )
    if result.returncode != 0:
        raise RuntimeError(f"cmake configure failed:\n{result.stdout}\n{result.stderr}")
    result = subprocess.run(
        ["cmake", "--build", str(BUILD_DIR)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cmake build failed:\n{result.stdout}\n{result.stderr}")
    return BINARY


def _run(*args: str, **kwargs) -> subprocess.CompletedProcess:
    binary = _build_binary()
    return subprocess.run(
        [str(binary), *args],
        capture_output=True, text=True, timeout=30, **kwargs,
    )


def test_round_trip() -> None:
    result = _run("test")
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_write_jeff_then_read_back() -> None:
    tmp = "/tmp/jeff_test_write.jeff"
    result = _run("write", tmp, "3", "2")
    assert result.returncode == 0, f"write failed: {result.stderr}"
    assert os.path.exists(tmp)

    result = _run("read", tmp)
    assert result.returncode == 0, f"read failed: {result.stderr}"
    assert f"3 qubits, 2 clbits" in result.stdout
    os.unlink(tmp)


def test_error_no_qubits_jeff() -> None:
    tmp = "/tmp/jeff_test_empty.jeff"
    result = _run("write", tmp, "0", "0")
    assert result.returncode != 0
    assert "no qubits" in result.stderr
    if os.path.exists(tmp):
        os.unlink(tmp)
