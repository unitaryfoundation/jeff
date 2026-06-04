"""CLI entry point for the jeff ↔ Qiskit converter."""

import sys
from pathlib import Path

from .converter import jeff_to_qiskit, qiskit_to_jeff


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m tools.qiskit_convert test         Run round-trip tests")
        print("  python -m tools.qiskit_convert read <jeff>   Convert jeff → Qiskit")
        print(
            "  python -m tools.qiskit_convert write <qasm> <jeff>  Convert QASM → jeff"
        )
        return 1

    command = sys.argv[1]

    if command == "test":
        from .tests.test_converter import run_tests

        return run_tests()

    if command == "read":
        if len(sys.argv) < 3:
            print("Error: missing jeff file path")
            return 1
        qc, lib, c_ptr = jeff_to_qiskit(Path(sys.argv[2]))
        print(qc)
        lib.free_circuit(c_ptr)
        return 0

    if command == "write":
        if len(sys.argv) < 4:
            print("Error: usage: write <qasm_file> <jeff_output>")
            return 1
        from qiskit import QuantumCircuit

        qc = QuantumCircuit.from_qasm_file(sys.argv[2])
        qiskit_to_jeff(qc, sys.argv[3])
        print(f"Wrote {sys.argv[3]}")
        return 0

    print(f"Error: unknown command '{command}'")
    return 1


if __name__ == "__main__":
    sys.exit(main())
