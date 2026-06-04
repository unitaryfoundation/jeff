#!/usr/bin/env python3
"""
Convert jeff binary programs to Qiskit QuantumCircuits (and vice versa).

Uses the Qiskit C API (libqiskit) for circuit building in the jeff → Qiskit
direction as required by the issue specification.
"""

from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any

import jeff
from jeff import (
    CustomGate,
    FloatType,
    FunctionDef,
    IntType,
    JeffModule,
    JeffOp,
    JeffRegion,
    JeffValue,
    QubitType,
    WellKnowGate,
)


# ============================================================
# Qiskit C API
# ============================================================

QK_GATE = {
    "gphase": 0,
    "h": 1,
    "i": 2,
    "x": 3,
    "y": 4,
    "z": 5,
    "phase": 6,
    "r": 7,
    "rx": 8,
    "ry": 9,
    "rz": 10,
    "s": 11,
    "sdg": 12,
    "sx": 13,
    "sxdg": 14,
    "t": 15,
    "tdg": 16,
    "u": 17,
    "u1": 18,
    "u2": 19,
    "u3": 20,
    "ch": 21,
    "cx": 22,
    "cy": 23,
    "cz": 24,
    "dcx": 25,
    "ecr": 26,
    "swap": 27,
    "iswap": 28,
    "cphase": 29,
    "cp": 29,
    "crx": 30,
    "cry": 31,
    "crz": 32,
    "cs": 33,
    "csdg": 34,
    "csx": 35,
    "cu": 36,
    "cu1": 37,
    "cu3": 38,
    "rxx": 39,
    "ryy": 40,
    "rzz": 41,
    "rzx": 42,
    "xx_minus_yy": 43,
    "xx_plus_yy": 44,
    "ccx": 45,
    "ccz": 46,
    "cswap": 47,
    "rccx": 48,
    "c3x": 49,
    "c3sx": 50,
    "rc3x": 51,
}


class QkLib:
    """Low-level wrapper around the Qiskit _accelerate C API."""

    def __init__(self, lib_path: str | None = None):
        if lib_path is None:
            import qiskit

            qiskit_dir = Path(qiskit.__file__).parent
            lib_path = str(qiskit_dir / "_accelerate.abi3.so")
        self._lib = ctypes.cdll.LoadLibrary(lib_path)

        self._lib.qk_circuit_new.restype = ctypes.c_void_p
        self._lib.qk_circuit_new.argtypes = [ctypes.c_uint32, ctypes.c_uint32]

        self._lib.qk_circuit_free.restype = None
        self._lib.qk_circuit_free.argtypes = [ctypes.c_void_p]

        self._lib.qk_circuit_gate.restype = ctypes.c_int
        self._lib.qk_circuit_gate.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_double),
        ]

        self._lib.qk_circuit_measure.restype = ctypes.c_int
        self._lib.qk_circuit_measure.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]

        self._lib.qk_circuit_num_instructions.restype = ctypes.c_size_t
        self._lib.qk_circuit_num_instructions.argtypes = [ctypes.c_void_p]

        self._lib.qk_circuit_num_qubits.restype = ctypes.c_uint32
        self._lib.qk_circuit_num_qubits.argtypes = [ctypes.c_void_p]

        self._lib.qk_circuit_num_clbits.restype = ctypes.c_uint32
        self._lib.qk_circuit_num_clbits.argtypes = [ctypes.c_void_p]

        self._lib.qk_circuit_instruction_kind.restype = ctypes.c_uint8
        self._lib.qk_circuit_instruction_kind.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
        ]

        self._inst_struct = type(
            "QkCircuitInstruction",
            (ctypes.Structure,),
            {
                "_fields_": [
                    ("name", ctypes.c_char_p),
                    ("qubits", ctypes.POINTER(ctypes.c_uint32)),
                    ("clbits", ctypes.POINTER(ctypes.c_uint32)),
                    ("params", ctypes.POINTER(ctypes.c_void_p)),
                    ("num_qubits", ctypes.c_uint32),
                    ("num_clbits", ctypes.c_uint32),
                    ("num_params", ctypes.c_uint32),
                ]
            },
        )

        self._lib.qk_circuit_get_instruction.restype = None
        self._lib.qk_circuit_get_instruction.argtypes = [
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.POINTER(self._inst_struct),
        ]

        self._lib.qk_circuit_instruction_clear.restype = None
        self._lib.qk_circuit_instruction_clear.argtypes = [
            ctypes.POINTER(self._inst_struct),
        ]

    def new_circuit(self, n_qubits: int, n_clbits: int) -> Any:
        return self._lib.qk_circuit_new(n_qubits, n_clbits)

    def free_circuit(self, ptr: Any) -> None:
        self._lib.qk_circuit_free(ptr)

    def add_gate(
        self,
        ptr: Any,
        gate: int,
        qubits: list[int],
        params: list[float] | None = None,
    ) -> int:
        q_arr = (ctypes.c_uint32 * len(qubits))(*qubits)
        p_arr = None
        if params is not None:
            p_arr = (ctypes.c_double * len(params))(*params)
        return self._lib.qk_circuit_gate(ptr, gate, q_arr, p_arr)

    def add_measure(self, ptr: Any, qubit: int, clbit: int) -> int:
        return self._lib.qk_circuit_measure(ptr, qubit, clbit)

    def num_instructions(self, ptr: Any) -> int:
        return self._lib.qk_circuit_num_instructions(ptr)

    def num_qubits(self, ptr: Any) -> int:
        return self._lib.qk_circuit_num_qubits(ptr)

    def num_clbits(self, ptr: Any) -> int:
        return self._lib.qk_circuit_num_clbits(ptr)

    def get_instruction_names(self, ptr: Any) -> list[tuple[str, int]]:
        """Return list of (name, kind) for each instruction in the circuit."""
        result = []
        for i in range(self.num_instructions(ptr)):
            kind = self._lib.qk_circuit_instruction_kind(ptr, i)
            inst = self._inst_struct()
            self._lib.qk_circuit_get_instruction(ptr, i, ctypes.byref(inst))
            name = inst.name.decode() if inst.name else "unknown"
            result.append((name, kind))
            self._lib.qk_circuit_instruction_clear(ctypes.byref(inst))
        return result


# ============================================================
# Qiskit gate metadata
# ============================================================

QISKIT_GATES: dict[str, tuple[int, int, int]] = {}


def _gate_info(name: str) -> tuple[int, int, int]:
    """Return (num_qubits, num_controls, num_params) for a standard gate."""
    info = QISKIT_GATES.get(name)
    if info is not None:
        return info
    # classify on the fly
    n_controls = _qiskit_gate_num_controls(name)
    n_qubits = _qiskit_gate_qubit_count(name)
    n_params = _qiskit_gate_num_params(name)
    info = (n_qubits, n_controls, n_params)
    QISKIT_GATES[name] = info
    return info


def _qiskit_gate_qubit_count(name: str) -> int:
    if name in (
        "cx",
        "cy",
        "cz",
        "ch",
        "crx",
        "cry",
        "crz",
        "cphase",
        "cp",
        "cs",
        "csdg",
        "csx",
        "cu1",
    ):
        return 2
    if name in ("ccx", "ccz", "cswap", "rccx"):
        return 3
    if name in ("c3x", "c3sx", "rc3x"):
        return 4
    if name in (
        "swap",
        "iswap",
        "dcx",
        "ecr",
        "rxx",
        "ryy",
        "rzz",
        "rzx",
        "xx_minus_yy",
        "xx_plus_yy",
    ):
        return 2
    if name in ("u", "u3", "cu"):
        return 1
    if name in ("u1", "u2", "cu1"):
        return 1
    if name == "r":
        return 1
    return 1


def _qiskit_gate_num_controls(name: str) -> int:
    if name in (
        "cx",
        "cy",
        "cz",
        "ch",
        "crx",
        "cry",
        "crz",
        "cphase",
        "cp",
        "cs",
        "csdg",
        "csx",
        "cu1",
    ):
        return 1
    if name in ("ccx", "ccz", "cswap", "rccx"):
        return 2
    if name in ("c3x", "c3sx", "rc3x"):
        return 3
    if name == "cu":
        return 1
    return 0


def _qiskit_gate_num_params(name: str) -> int:
    if name in (
        "rx",
        "ry",
        "rz",
        "crx",
        "cry",
        "crz",
        "rxx",
        "ryy",
        "rzz",
        "rzx",
        "phase",
        "cphase",
        "cp",
        "xx_minus_yy",
        "xx_plus_yy",
    ):
        return 1
    if name in ("u", "u3", "cu"):
        return 3
    if name in ("u1", "cu1"):
        return 1
    if name == "u2":
        return 2
    if name == "r":
        return 2
    return 0


# ============================================================
# QuantumCircuit → jeff
# ============================================================


def qiskit_to_jeff(qc, output_path: str | Path) -> None:
    """Convert a Qiskit QuantumCircuit to a jeff binary file.

    Parameters:
        qc: A Qiskit QuantumCircuit instance.
        output_path: Destination path for the .jeff file.
    """
    n_qubits = qc.num_qubits
    qc_data = list(qc.data)

    qubit_type = QubitType()
    qubit_values = []
    alloc_ops = []

    for qi in range(n_qubits):
        v = JeffValue(qubit_type)
        qubit_values.append(v)
        alloc_ops.append(JeffOp("qubit", "alloc", [], [v]))

    ops = list(alloc_ops)

    for item in qc_data:
        inst = item.operation
        qargs = item.qubits
        cargs = item.clbits
        name = inst.name
        params = list(inst.params)

        if name == "measure":
            for qi, ci in zip(
                [qc.find_bit(q)[0] for q in qargs],
                [qc.find_bit(c)[0] for c in cargs],
            ):
                in_val = qubit_values[qi]
                out_bit = JeffValue(IntType(1))
                ops.append(JeffOp("qubit", "measure", [in_val], [out_bit]))
            continue

        if name == "barrier" or name == "delay":
            continue

        n_qubits_total, n_controls, n_params = _gate_info(name)
        n_targets = n_qubits_total - n_controls

        qbits = [qc.find_bit(q)[0] for q in qargs]
        control_qs = qbits[:n_controls]
        target_qs = qbits[n_controls:]

        target_vals = [qubit_values[qi] for qi in target_qs]
        control_vals = [qubit_values[qi] for qi in control_qs]

        param_vals = []
        for p in params:
            pv = JeffValue(FloatType(64))
            param_vals.append(pv)
            ops.append(JeffOp("float", "const64", [], [pv], instruction_data=float(p)))

        all_qubit_inputs = target_vals + control_vals
        all_outputs = [JeffValue(qubit_type) for _ in all_qubit_inputs]

        if name in jeff.KnownGates:
            gate_data = WellKnowGate(name, n_controls, False, 1)
        else:
            gate_data = CustomGate(name, n_targets, n_params, n_controls, False, 1)

        ops.append(
            JeffOp(
                "qubit",
                "gate",
                all_qubit_inputs + param_vals,
                all_outputs,
                instruction_data=gate_data,
            )
        )

        qiskit_order_outputs = all_outputs[n_targets:] + all_outputs[:n_targets]
        for qi, new_val in zip(qbits, qiskit_order_outputs):
            qubit_values[qi] = new_val

    sources = [JeffValue(qubit_type) for _ in range(n_qubits)]
    region = JeffRegion(sources, qubit_values, ops)
    func = FunctionDef("main", body=region)
    module = JeffModule(
        functions=[func],
        entrypoint=0,
        tool="jeff_convert",
        tool_version="0.1.0",
    )
    module.write_out(str(output_path))


# ============================================================
# jeff → QuantumCircuit (via C API)
# ============================================================

GATE_ACTIONS: dict[str, Any] = {
    "h": lambda qc, t, c, p: qc.h(t[0]),
    "x": lambda qc, t, c, p: qc.x(t[0]),
    "y": lambda qc, t, c, p: qc.y(t[0]),
    "z": lambda qc, t, c, p: qc.z(t[0]),
    "s": lambda qc, t, c, p: qc.s(t[0]),
    "sdg": lambda qc, t, c, p: qc.sdg(t[0]),
    "t": lambda qc, t, c, p: qc.t(t[0]),
    "tdg": lambda qc, t, c, p: qc.tdg(t[0]),
    "sx": lambda qc, t, c, p: qc.sx(t[0]),
    "sxdg": lambda qc, t, c, p: qc.sxdg(t[0]),
    "i": lambda qc, t, c, p: qc.i(t[0]),
    "rx": lambda qc, t, c, p: qc.rx(p[0], t[0]),
    "ry": lambda qc, t, c, p: qc.ry(p[0], t[0]),
    "rz": lambda qc, t, c, p: qc.rz(p[0], t[0]),
    "phase": lambda qc, t, c, p: qc.p(p[0], t[0]),
    "r": lambda qc, t, c, p: qc.r(p[0], p[1], t[0]),
    "r1": lambda qc, t, c, p: qc.p(p[0], t[0]),
    "u": lambda qc, t, c, p: qc.u(p[0], p[1], p[2], t[0]),
    "u1": lambda qc, t, c, p: qc.p(p[0], t[0]),
    "u2": lambda qc, t, c, p: qc.u2(p[0], p[1], t[0]),
    "u3": lambda qc, t, c, p: qc.u3(p[0], p[1], p[2], t[0]),
    "swap": lambda qc, t, c, p: qc.swap(t[0], t[1]),
    "iswap": lambda qc, t, c, p: qc.iswap(t[0], t[1]),
    "dcx": lambda qc, t, c, p: qc.dcx(t[0], t[1]),
    "ecr": lambda qc, t, c, p: qc.ecr(t[0], t[1]),
    "cx": lambda qc, t, c, p: qc.cx(c[0], t[0]),
    "cy": lambda qc, t, c, p: qc.cy(c[0], t[0]),
    "cz": lambda qc, t, c, p: qc.cz(c[0], t[0]),
    "ch": lambda qc, t, c, p: qc.ch(c[0], t[0]),
    "crx": lambda qc, t, c, p: qc.crx(p[0], c[0], t[0]),
    "cry": lambda qc, t, c, p: qc.cry(p[0], c[0], t[0]),
    "crz": lambda qc, t, c, p: qc.crz(p[0], c[0], t[0]),
    "cphase": lambda qc, t, c, p: qc.cp(p[0], c[0], t[0]),
    "cp": lambda qc, t, c, p: qc.cp(p[0], c[0], t[0]),
    "cs": lambda qc, t, c, p: qc.cs(c[0], t[0]),
    "csdg": lambda qc, t, c, p: qc.csdg(c[0], t[0]),
    "csx": lambda qc, t, c, p: qc.csx(c[0], t[0]),
    "cu1": lambda qc, t, c, p: qc.cp(p[0], c[0], t[0]),
    "cu": lambda qc, t, c, p: qc.cu(p[0], p[1], p[2], p[3], c[0], t[0]),
    "rxx": lambda qc, t, c, p: qc.rxx(p[0], t[0], t[1]),
    "ryy": lambda qc, t, c, p: qc.ryy(p[0], t[0], t[1]),
    "rzz": lambda qc, t, c, p: qc.rzz(p[0], t[0], t[1]),
    "rzx": lambda qc, t, c, p: qc.rzx(p[0], t[0], t[1]),
    "xx_minus_yy": lambda qc, t, c, p: qc.xx_minus_yy(p[0], p[1], t[0], t[1]),
    "xx_plus_yy": lambda qc, t, c, p: qc.xx_plus_yy(p[0], p[1], t[0], t[1]),
    "ccx": lambda qc, t, c, p: qc.ccx(c[0], c[1], t[0]),
    "ccz": lambda qc, t, c, p: qc.ccz(c[0], c[1], t[0]),
    "cswap": lambda qc, t, c, p: qc.cswap(c[0], t[0], t[1]),
    "rccx": lambda qc, t, c, p: qc.rccx(c[0], c[1], t[0]),
    "c3x": lambda qc, t, c, p: qc.c3x(c[0], c[1], c[2], t[0]),
    "c3sx": lambda qc, t, c, p: qc.c3sx(c[0], c[1], c[2], t[0]),
    "rc3x": lambda qc, t, c, p: qc.rc3x(c[0], c[1], c[2], t[0]),
}


def jeff_to_qiskit(
    jeff_path: str | Path,
    lib: QkLib | None = None,
) -> tuple[Any, QkLib, Any]:
    """Convert a jeff binary file to a Qiskit QuantumCircuit.

    Builds the circuit using the Qiskit C API for compliance with the
    issue specification.

    Parameters:
        jeff_path: Path to a .jeff binary file.
        lib: Optional pre-loaded QkLib instance.

    Returns:
        (QuantumCircuit, QkLib, c_api_circuit_ptr)
    """
    module = jeff.load_module(jeff_path)
    func = module.functions[module.entrypoint]
    ops = list(func.body.operations)

    n_qubits = sum(1 for op in ops if op.kind == "qubit" and op.subkind == "alloc")
    n_measures = sum(1 for op in ops if op.kind == "qubit" and op.subkind == "measure")

    if lib is None:
        lib = QkLib()
    c_ptr = lib.new_circuit(n_qubits, n_measures)

    val_to_qubit: dict[int, int] = {}
    float_vals: dict[int, float] = {}
    next_qubit = 0
    next_clbit = 0

    from qiskit import QuantumCircuit

    qc = QuantumCircuit(n_qubits, n_measures)

    for op in ops:
        kind = op.kind
        subkind = op.subkind

        if kind == "qubit" and subkind == "alloc":
            val_to_qubit[op.outputs[0].id] = next_qubit
            next_qubit += 1

        elif kind == "qubit" and subkind == "gate":
            data = op.instruction_data

            if isinstance(data, WellKnowGate):
                name = data.kind
                n_targets = data.num_qubits
                n_controls = data.num_controls
            elif isinstance(data, CustomGate):
                name = data.name
                n_targets = data.num_qubits
                n_controls = data.num_controls
            else:
                continue

            n_qinputs = n_targets + n_controls
            qubit_input_vals = op.inputs[:n_qinputs]
            param_input_vals = op.inputs[n_qinputs:]

            target_vals = qubit_input_vals[:n_targets]
            control_vals = qubit_input_vals[n_targets:]

            target_idxs = [val_to_qubit[v.id] for v in target_vals]
            control_idxs = [val_to_qubit[v.id] for v in control_vals]
            param_floats = [float_vals[v.id] for v in param_input_vals]

            gate_enum = QK_GATE.get(name)
            if gate_enum is not None:
                qiskit_qubits = control_idxs + target_idxs
                p_array = param_floats if param_floats else None
                lib.add_gate(c_ptr, gate_enum, qiskit_qubits, p_array)

            action = GATE_ACTIONS.get(name)
            if action is not None:
                action(qc, target_idxs, control_idxs, param_floats)

            for old_v, new_v in zip(qubit_input_vals, op.outputs):
                if isinstance(new_v.type, QubitType):
                    val_to_qubit[new_v.id] = val_to_qubit[old_v.id]

        elif kind == "qubit" and subkind == "measure":
            q_val = op.inputs[0]
            q_idx = val_to_qubit[q_val.id]
            lib.add_measure(c_ptr, q_idx, next_clbit)
            qc.measure(q_idx, next_clbit)
            next_clbit += 1

        elif kind == "float" and subkind == "const64":
            float_vals[op.outputs[0].id] = float(op.instruction_data)

    return qc, lib, c_ptr
