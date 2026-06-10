import sys
from pathlib import Path
import pytest

# Add the compiled extension and py package to the Python path
REPO_ROOT = Path(__file__).parent.parent.parent.parent
BUILD_DIR = REPO_ROOT / "tools" / "qiskit_convert" / "build"
sys.path.insert(0, str(BUILD_DIR))
sys.path.insert(0, str(REPO_ROOT / "impl" / "py" / "src"))

import qiskit_jeff_py
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
import math


def test_qiskit_to_jeff_to_qiskit():
    # 1. Create a Qiskit circuit
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.rx(math.pi / 2, 0)
    qc.ry(math.pi / 4, 1)
    qc.measure([0, 1], [0, 1])

    # 2. Convert to jeff binary format
    jeff_binary = qiskit_jeff_py.qiskit_to_jeff(qc)
    assert isinstance(jeff_binary, bytes)
    assert len(jeff_binary) > 0

    # 3. Convert back to Qiskit circuit
    qc_roundtrip = qiskit_jeff_py.jeff_to_qiskit(jeff_binary)
    assert isinstance(qc_roundtrip, QuantumCircuit)

    # 4. Verify structural equality
    assert qc.num_qubits == qc_roundtrip.num_qubits
    assert qc.num_clbits == qc_roundtrip.num_clbits

    # Wait, the Qiskit C API doesn't support named registers so the roundtrip might drop register names,
    # but the instructions and their data should match.
    # Qiskit equivalence check:
    # Actually Qiskit has a problem comparing circuits with no named registers vs named ones.
    # We can compare qasm or counts.
    ops_orig = dict(qc.count_ops())
    ops_round = dict(qc_roundtrip.count_ops())
    assert ops_orig == ops_round

    # The depth should match
    assert qc.depth() == qc_roundtrip.depth()


def test_unsupported_gate():
    # 1. Create a Qiskit circuit with unsupported gate (e.g., something we didn't map yet)
    qc = QuantumCircuit(1)
    # We didn't map rccx yet, wait rccx is 3 qubits.
    # Let's map something simple like sx
    qc.sx(0)

    # 2. Verify conversion throws RuntimeError
    with pytest.raises(RuntimeError):
        qiskit_jeff_py.qiskit_to_jeff(qc)
