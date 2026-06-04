"""Tests for the jeff ↔ Qiskit converter."""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import pytest

from ..converter import QkLib, jeff_to_qiskit, qiskit_to_jeff


def _check_roundtrip(qc_orig, lib: QkLib) -> bool:
    """Round-trip a circuit through jeff and verify equivalence."""
    with tempfile.NamedTemporaryFile(suffix=".jeff", delete=False) as f:
        jeff_path = f.name

    try:
        qiskit_to_jeff(qc_orig, jeff_path)
        qc_result, _, c_ptr = jeff_to_qiskit(jeff_path, lib)

        orig_ops = dict(qc_orig.count_ops())
        result_ops = dict(qc_result.count_ops())

        qubits_ok = qc_orig.num_qubits == qc_result.num_qubits
        clbits_ok = qc_orig.num_clbits == qc_result.num_clbits
        ops_ok = orig_ops == result_ops

        capi_names = [n for n, _ in lib.get_instruction_names(c_ptr)]
        capi_counts: dict[str, int] = {}
        for n in capi_names:
            capi_counts[n] = capi_counts.get(n, 0) + 1
        capi_ok = capi_counts == orig_ops

        lib.free_circuit(c_ptr)
        return qubits_ok and clbits_ok and ops_ok and capi_ok
    finally:
        Path(jeff_path).unlink(missing_ok=True)


# ---- Test cases ----


def test_issue_example(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.x(0)
    qc.x(1)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(-2 * math.pi / 3, 1)
    qc.measure([0, 1], [0, 1])
    assert _check_roundtrip(qc, lib)


def test_single_qubit_hst(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.s(0)
    qc.t(0)
    qc.measure(0, 0)
    assert _check_roundtrip(qc, lib)


def test_single_qubit_xyz(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1, 1)
    qc.x(0)
    qc.y(0)
    qc.z(0)
    qc.measure(0, 0)
    assert _check_roundtrip(qc, lib)


def test_bell_state_reverse_cx(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 0)
    qc.measure([0, 1], [0, 1])
    assert _check_roundtrip(qc, lib)


def test_three_qubit_ccx(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3, 0)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.ccx(0, 1, 2)
    assert _check_roundtrip(qc, lib)


def test_single_qubit_rotations(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1, 0)
    qc.rx(0.5, 0)
    qc.ry(1.0, 0)
    qc.rz(1.5, 0)
    assert _check_roundtrip(qc, lib)


def test_swap_gate(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.swap(0, 1)
    qc.measure([0, 1], [0, 1])
    assert _check_roundtrip(qc, lib)


def test_controlled_rotations(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.crx(0.5, 0, 1)
    qc.cry(1.0, 0, 1)
    qc.crz(1.5, 0, 1)
    assert _check_roundtrip(qc, lib)


def test_cphase_gate(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.cp(0.5, 0, 1)
    assert _check_roundtrip(qc, lib)


def test_sxdg_and_iswap(lib: QkLib) -> None:
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.sx(0)
    qc.sxdg(1)
    qc.iswap(0, 1)
    assert _check_roundtrip(qc, lib)


# ---- Fixtures ----


@pytest.fixture(scope="session")
def lib() -> QkLib:
    return QkLib()


# ---- Standalone runner ----


def run_tests() -> int:
    """Run all tests (used by __main__.py)."""
    lib = QkLib()
    from qiskit import QuantumCircuit

    cases = [
        ("Issue example", lambda: _make_issue_example()),
        (
            "Single HST",
            lambda: _make_simple(QuantumCircuit(1, 1), ["h", "s", "t", "meas"]),
        ),
        (
            "Single XYZ",
            lambda: _make_simple(QuantumCircuit(1, 1), ["x", "y", "z", "meas"]),
        ),
        ("Bell reverse", lambda: _make_bell_reverse()),
        ("3-qubit CCX", lambda: _make_ccx()),
        ("Rotations", lambda: _make_rotations()),
        ("SWAP", lambda: _make_swap()),
        ("Controlled rotations", lambda: _make_crotations()),
        ("CPhase", lambda: _make_cphase()),
        ("SXdg+ISwap", lambda: _make_sxdg_iswap()),
    ]

    passed = 0
    failed = 0
    for label, maker in cases:
        qc = maker()
        ok = _check_roundtrip(qc, lib)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{passed}/{passed + failed} passed")
    return 0 if failed == 0 else 1


def _make_issue_example():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.x(0)
    qc.x(1)
    qc.h(0)
    qc.cx(0, 1)
    qc.ry(-2 * math.pi / 3, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def _make_simple(qc, gates):
    for g in gates:
        if g == "meas":
            qc.measure(0, 0)
        else:
            getattr(qc, g)(0)
    return qc


def _make_bell_reverse():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 0)
    qc.measure([0, 1], [0, 1])
    return qc


def _make_ccx():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3, 0)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.ccx(0, 1, 2)
    return qc


def _make_rotations():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(1, 0)
    qc.rx(0.5, 0)
    qc.ry(1.0, 0)
    qc.rz(1.5, 0)
    return qc


def _make_swap():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 2)
    qc.swap(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def _make_crotations():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.crx(0.5, 0, 1)
    qc.cry(1.0, 0, 1)
    qc.crz(1.5, 0, 1)
    return qc


def _make_cphase():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.cp(0.5, 0, 1)
    return qc


def _make_sxdg_iswap():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(2, 0)
    qc.sx(0)
    qc.sxdg(1)
    qc.iswap(0, 1)
    return qc
