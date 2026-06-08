from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

try:
    import qiskit
except ImportError:
    pytest.skip(
        "Qiskit is not installed — skipping qiskit_convert tests",
        allow_module_level=True,
    )


def _run(converter: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(converter), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def _build_circuit(n_qubits: int, n_clbits: int) -> qiskit.QuantumCircuit:
    qc = qiskit.QuantumCircuit(n_qubits, n_clbits)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(-2.0 * 3.141592653589793 / 3.0, 1)
    qc.measure_all()
    return qc


def test_converter_builds(converter: Path) -> None:
    assert converter.exists()
    assert os.access(str(converter), os.X_OK)


def test_write_generates_jeff(converter: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".jeff", delete=False) as f:
        tmp = f.name
    try:
        result = _run(converter, "write", tmp, "3", "2")
        assert result.returncode == 0, f"write failed: {result.stderr}"
        assert os.path.exists(tmp)
        assert os.path.getsize(tmp) > 0
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_read_back_jeff(converter: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".jeff", delete=False) as f:
        tmp = f.name
    try:
        result = _run(converter, "write", tmp, "3", "2")
        assert result.returncode == 0, f"write failed: {result.stderr}"

        result = _run(converter, "read", tmp)
        assert result.returncode == 0, f"read failed: {result.stderr}"
        assert "3 qubits, 2 clbits" in result.stdout
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_error_no_qubits(converter: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".jeff", delete=False) as f:
        tmp = f.name
    try:
        result = _run(converter, "write", tmp, "0", "0")
        assert result.returncode != 0
        assert "no qubits" in result.stderr
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
