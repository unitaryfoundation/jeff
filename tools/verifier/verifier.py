"""Validation helpers for encoded jeff modules."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jeff import schema


@dataclass(frozen=True)
class VerificationError:
    """A single validation error."""

    path: str
    message: str


@dataclass(frozen=True)
class _Type:
    kind: str
    width: int | None = None
    precision: int | None = None
    length: int | None = None


_INT_CONST_WIDTHS = {
    "const1": 1,
    "const8": 8,
    "const16": 16,
    "const32": 32,
    "const64": 64,
}

_INT_BINARY_SAME = {
    "add",
    "sub",
    "mul",
    "divS",
    "divU",
    "pow",
    "and",
    "or",
    "xor",
    "minS",
    "minU",
    "maxS",
    "maxU",
    "remS",
    "remU",
    "shl",
    "shr",
}

_INT_BINARY_BOOL = {"eq", "ltS", "lteS", "ltU", "lteU"}
_INT_UNARY_SAME = {"not", "abs"}

_INT_ARRAY_CONST_WIDTHS = _INT_CONST_WIDTHS

_FLOAT_CONST_PRECISIONS = {"const32": 32, "const64": 64}
_FLOAT_BINARY_SAME = {"add", "sub", "mul", "pow", "atan2", "max", "min"}
_FLOAT_BINARY_BOOL = {"eq", "lt", "lte"}
_FLOAT_UNARY_SAME = {
    "sqrt",
    "abs",
    "ceil",
    "floor",
    "exp",
    "log",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "sinh",
    "cosh",
    "tanh",
    "asinh",
    "acosh",
    "atanh",
}
_FLOAT_UNARY_BOOL = {"isNan", "isInf"}

_FLOAT_ARRAY_CONST_PRECISIONS = _FLOAT_CONST_PRECISIONS

_WELL_KNOWN_GATES = {
    "gphase": (0, 1),
    "i": (1, 0),
    "x": (1, 0),
    "y": (1, 0),
    "z": (1, 0),
    "s": (1, 0),
    "t": (1, 0),
    "r1": (1, 1),
    "rx": (1, 1),
    "ry": (1, 1),
    "rz": (1, 1),
    "h": (1, 0),
    "u": (1, 3),
    "swap": (2, 0),
}


def verify_file(path: Path | str) -> list[VerificationError]:
    """Verify an encoded jeff module stored on disk."""

    try:
        with open(path, "rb") as file:
            module = schema.Module.read(file)
    except Exception as exc:  # noqa: BLE001
        return [VerificationError(str(path), f"could not read jeff module: {exc}")]

    return verify_module(module)


def verify_module(module: Any) -> list[VerificationError]:
    """Verify an encoded jeff module."""

    verifier = _ModuleVerifier(module)
    return verifier.verify()


def _type_from_value(value: Any) -> _Type:
    type_data = value.type
    kind = str(type_data.which)

    if kind == "qubit":
        return _Type("qubit")
    if kind == "qureg":
        length = (
            type_data.qureg.static if str(type_data.qureg.which) == "static" else None
        )
        return _Type("qureg", length=length)
    if kind == "int":
        return _Type("int", width=int(type_data.int))
    if kind == "intArray":
        length = (
            type_data.intArray.length.static
            if str(type_data.intArray.length.which) == "static"
            else None
        )
        return _Type("intArray", width=int(type_data.intArray.bitwidth), length=length)
    if kind == "float":
        return _Type("float", precision=_precision(type_data.float))
    if kind == "floatArray":
        length = (
            type_data.floatArray.length.static
            if str(type_data.floatArray.length.which) == "static"
            else None
        )
        return _Type(
            "floatArray",
            precision=_precision(type_data.floatArray.precision),
            length=length,
        )

    return _Type(kind)


def _precision(value: Any) -> int:
    precision = str(value)
    if precision == "float32":
        return 32
    if precision == "float64":
        return 64
    raise ValueError(f"unknown float precision: {precision}")


def _format_type(type_: _Type | None) -> str:
    if type_ is None:
        return "<invalid>"
    if type_.kind == "int":
        return f"int({type_.width})"
    if type_.kind == "intArray":
        length = "?" if type_.length is None else str(type_.length)
        return f"intArray({type_.width}, {length})"
    if type_.kind == "float":
        return f"float({type_.precision})"
    if type_.kind == "floatArray":
        length = "?" if type_.length is None else str(type_.length)
        return f"floatArray({type_.precision}, {length})"
    if type_.kind == "qureg":
        length = "?" if type_.length is None else str(type_.length)
        return f"qureg({length})"
    return type_.kind


def _is_linear(type_: _Type | None) -> bool:
    return type_ is not None and type_.kind in {"qubit", "qureg"}


def _same_type(left: _Type | None, right: _Type | None) -> bool:
    return left is not None and right is not None and left == right


class _ModuleVerifier:
    def __init__(self, module: Any):
        self.module = module
        self.errors: list[VerificationError] = []
        self._function_signature_cache: dict[
            int, tuple[list[_Type], list[_Type]] | None
        ] = {}

    def verify(self) -> list[VerificationError]:
        self._check_module()
        for index, function in enumerate(self.module.functions):
            self._check_function(index, function)
        return self.errors

    def _error(self, path: str, message: str) -> None:
        self.errors.append(VerificationError(path, message))

    def _check_module(self) -> None:
        path = "module"
        version = (
            int(self.module.version),
            int(self.module.versionMinor),
            int(self.module.versionPatch),
        )
        expected = (
            int(schema.schemaVersionMajor),
            int(schema.schemaVersionMinor),
            int(schema.schemaVersionPatch),
        )
        if version != expected:
            self._error(
                path, f"unsupported schema version {version}, expected {expected}"
            )

        if len(self.module.functions) == 0:
            self._error(path, "module must contain at least one function")
        elif self.module.entrypoint >= len(self.module.functions):
            self._error(
                f"{path}.entrypoint",
                f"entrypoint {self.module.entrypoint} is outside functions list",
            )

        names: dict[str, int] = {}
        for index, function in enumerate(self.module.functions):
            name_path = f"module.functions[{index}].name"
            if function.name >= len(self.module.strings):
                self._error(name_path, f"string index {function.name} is out of range")
                continue

            name = self.module.strings[function.name]
            if name in names:
                self._error(name_path, f"duplicate function name {name!r}")
            names[name] = index

    def _check_function(self, index: int, function: Any) -> None:
        path = f"module.functions[{index}]"
        kind = str(function.which)
        if kind == "declaration":
            self._check_value_types(function.declaration.inputs, f"{path}.inputs")
            self._check_value_types(function.declaration.outputs, f"{path}.outputs")
            return

        if kind != "definition":
            self._error(path, f"unknown function variant {kind!r}")
            return

        values = [_type_from_value(value) for value in function.definition.values]
        function_verifier = _FunctionVerifier(self, index, values)
        function_verifier.check_region(
            function.definition.body, f"{path}.definition.body"
        )
        function_verifier.check_linearity()

    def _check_value_types(self, values: Any, path: str) -> None:
        for index, value in enumerate(values):
            try:
                _type_from_value(value)
            except Exception as exc:  # noqa: BLE001
                self._error(f"{path}[{index}]", f"invalid value type: {exc}")

    def function_signature(self, index: int) -> tuple[list[_Type], list[_Type]] | None:
        if index in self._function_signature_cache:
            return self._function_signature_cache[index]

        if index >= len(self.module.functions):
            self._function_signature_cache[index] = None
            return None

        function = self.module.functions[index]
        kind = str(function.which)
        if kind == "declaration":
            signature = (
                [_type_from_value(value) for value in function.declaration.inputs],
                [_type_from_value(value) for value in function.declaration.outputs],
            )
            self._function_signature_cache[index] = signature
            return signature

        if kind != "definition":
            self._function_signature_cache[index] = None
            return None

        values = [_type_from_value(value) for value in function.definition.values]
        sources = [
            values[source]
            for source in function.definition.body.sources
            if source < len(values)
        ]
        targets = [
            values[target]
            for target in function.definition.body.targets
            if target < len(values)
        ]
        signature = (sources, targets)
        self._function_signature_cache[index] = signature
        return signature


class _FunctionVerifier:
    def __init__(
        self, module: _ModuleVerifier, function_index: int, values: list[_Type]
    ):
        self.module = module
        self.function_index = function_index
        self.values = values
        self.linear_definitions: Counter[int] = Counter()
        self.linear_uses: Counter[int] = Counter()

    def check_region(self, region: Any, path: str) -> None:
        defined: set[int] = set()

        for source in region.sources:
            if self._check_value_index(source, f"{path}.sources"):
                defined.add(int(source))
                self._record_linear_definition(int(source))

        for op_index, op in enumerate(region.operations):
            op_path = f"{path}.operations[{op_index}]"
            inputs = [int(value) for value in op.inputs]
            outputs = [int(value) for value in op.outputs]

            for value in inputs:
                if not self._check_value_index(value, f"{op_path}.inputs"):
                    continue
                if value not in defined:
                    self.module._error(
                        f"{op_path}.inputs",
                        f"value {value} is used before it is defined in this region",
                    )
                self._record_linear_use(value)

            self._check_operation_types(op, inputs, outputs, op_path)

            for value in outputs:
                if not self._check_value_index(value, f"{op_path}.outputs"):
                    continue
                if value in defined:
                    self.module._error(
                        f"{op_path}.outputs",
                        f"value {value} is defined more than once in this region",
                    )
                defined.add(value)
                self._record_linear_definition(value)

        for target in region.targets:
            if not self._check_value_index(target, f"{path}.targets"):
                continue
            if int(target) not in defined:
                self.module._error(
                    f"{path}.targets",
                    f"value {target} escapes into the region without being defined there",
                )
            self._record_linear_use(int(target))

    def check_linearity(self) -> None:
        for value, definitions in sorted(self.linear_definitions.items()):
            uses = self.linear_uses[value]
            if definitions != 1:
                self.module._error(
                    f"module.functions[{self.function_index}].definition.values[{value}]",
                    f"linear value is defined {definitions} times",
                )
            if uses != 1:
                self.module._error(
                    f"module.functions[{self.function_index}].definition.values[{value}]",
                    f"linear value is used {uses} times, expected exactly once",
                )

    def _check_value_index(self, value: int, path: str) -> bool:
        if value >= len(self.values):
            self.module._error(path, f"value index {value} is out of range")
            return False
        return True

    def _type(self, value: int) -> _Type | None:
        if 0 <= value < len(self.values):
            return self.values[value]
        return None

    def _types(self, values: list[int]) -> list[_Type | None]:
        return [self._type(value) for value in values]

    def _record_linear_definition(self, value: int) -> None:
        if _is_linear(self._type(value)):
            self.linear_definitions[value] += 1

    def _record_linear_use(self, value: int) -> None:
        if _is_linear(self._type(value)):
            self.linear_uses[value] += 1

    def _check_operation_types(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.instruction.which)
        if kind == "qubit":
            self._check_qubit_op(op.instruction.qubit, inputs, outputs, path)
        elif kind == "qureg":
            self._check_qureg_op(op.instruction.qureg, inputs, outputs, path)
        elif kind == "int":
            self._check_int_op(op.instruction.int, inputs, outputs, path)
        elif kind == "intArray":
            self._check_int_array_op(op.instruction.intArray, inputs, outputs, path)
        elif kind == "float":
            self._check_float_op(op.instruction.float, inputs, outputs, path)
        elif kind == "floatArray":
            self._check_float_array_op(op.instruction.floatArray, inputs, outputs, path)
        elif kind == "scf":
            self._check_scf_op(op.instruction.scf, inputs, outputs, path)
        elif kind == "func":
            self._check_func_op(op.instruction.func, inputs, outputs, path)
        else:
            self.module._error(path, f"unknown instruction kind {kind!r}")

    def _check_qubit_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind == "alloc":
            self._expect_arity(inputs, outputs, 0, 1, path)
            self._expect_kind(outputs, 0, "qubit", path)
        elif kind in {"free", "freeZero"}:
            self._expect_arity(inputs, outputs, 1, 0, path)
            self._expect_kind(inputs, 0, "qubit", path)
        elif kind == "measure":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "qubit", path)
            self._expect_int_width(outputs, 0, 1, path)
        elif kind == "measureNd":
            self._expect_arity(inputs, outputs, 1, 2, path)
            self._expect_kind(inputs, 0, "qubit", path)
            self._expect_kind(outputs, 0, "qubit", path)
            self._expect_int_width(outputs, 1, 1, path)
        elif kind == "reset":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "qubit", path)
            self._expect_kind(outputs, 0, "qubit", path)
        elif kind == "gate":
            self._check_gate(op.gate, inputs, outputs, path)
        else:
            self.module._error(path, f"unknown qubit operation {kind!r}")

    def _check_gate(
        self, gate: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        gate_kind = str(gate.which)
        controls = int(gate.controlQubits)
        if gate_kind == "wellKnown":
            name = str(gate.wellKnown)
            if name not in _WELL_KNOWN_GATES:
                self.module._error(path, f"unknown well-known gate {name!r}")
                return
            qubits, params = _WELL_KNOWN_GATES[name]
        elif gate_kind == "custom":
            if gate.custom.name >= len(self.module.module.strings):
                self.module._error(
                    path, f"custom gate name index {gate.custom.name} is out of range"
                )
            qubits = int(gate.custom.numQubits)
            params = int(gate.custom.numParams)
        elif gate_kind == "ppr":
            qubits = len(gate.ppr.pauliString)
            params = 1
        else:
            self.module._error(path, f"unknown gate variant {gate_kind!r}")
            return

        qubit_inputs = qubits + controls
        self._expect_arity(inputs, outputs, qubit_inputs + params, qubit_inputs, path)
        for index in range(qubit_inputs):
            self._expect_kind(inputs, index, "qubit", path)
            self._expect_kind(outputs, index, "qubit", path)
        for index in range(qubit_inputs, qubit_inputs + params):
            self._expect_kind(inputs, index, "float", path)

    def _check_qureg_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind == "alloc":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_int_width(inputs, 0, 32, path)
            self._expect_kind(outputs, 0, "qureg", path)
        elif kind in {"free", "freeZero"}:
            self._expect_arity(inputs, outputs, 1, 0, path)
            self._expect_kind(inputs, 0, "qureg", path)
        elif kind == "extractIndex":
            self._expect_arity(inputs, outputs, 2, 2, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
            self._expect_kind(outputs, 1, "qubit", path)
        elif kind == "insertIndex":
            self._expect_arity(inputs, outputs, 3, 1, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_kind(inputs, 2, "qubit", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        elif kind == "extractSlice":
            self._expect_arity(inputs, outputs, 3, 2, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_int_width(inputs, 2, 32, path)
            self._expect_kind(outputs, 0, "qureg", path)
            self._expect_kind(outputs, 1, "qureg", path)
        elif kind == "insertSlice":
            self._expect_arity(inputs, outputs, 3, 1, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_kind(inputs, 2, "qureg", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        elif kind == "length":
            self._expect_arity(inputs, outputs, 1, 2, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
            self._expect_int_width(outputs, 1, 32, path)
        elif kind == "split":
            self._expect_arity(inputs, outputs, 2, 2, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_kind(outputs, 0, "qureg", path)
            self._expect_kind(outputs, 1, "qureg", path)
        elif kind == "join":
            self._expect_arity(inputs, outputs, 2, 1, path)
            self._expect_kind(inputs, 0, "qureg", path)
            self._expect_kind(inputs, 1, "qureg", path)
            self._expect_kind(outputs, 0, "qureg", path)
        elif kind == "create":
            self._expect_arity(inputs, outputs, None, 1, path)
            for index in range(len(inputs)):
                self._expect_kind(inputs, index, "qubit", path)
            self._expect_kind(outputs, 0, "qureg", path)
        else:
            self.module._error(path, f"unknown qureg operation {kind!r}")

    def _check_int_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind in _INT_CONST_WIDTHS:
            self._expect_arity(inputs, outputs, 0, 1, path)
            self._expect_int_width(outputs, 0, _INT_CONST_WIDTHS[kind], path)
        elif kind in _INT_BINARY_SAME:
            self._check_same_numeric_op(inputs, outputs, "int", False, path)
        elif kind in _INT_BINARY_BOOL:
            self._check_same_numeric_op(inputs, outputs, "int", True, path)
        elif kind in _INT_UNARY_SAME:
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "int", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        else:
            self.module._error(path, f"unknown integer operation {kind!r}")

    def _check_int_array_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind in _INT_ARRAY_CONST_WIDTHS:
            self._expect_arity(inputs, outputs, 0, 1, path)
            self._expect_array_width(
                outputs, 0, "intArray", _INT_ARRAY_CONST_WIDTHS[kind], path
            )
            self._expect_static_length(outputs, 0, len(getattr(op, kind)), path)
        elif kind == "zero":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_int_width(inputs, 0, 32, path)
            self._expect_array_width(outputs, 0, "intArray", int(op.zero), path)
        elif kind == "getIndex":
            self._expect_arity(inputs, outputs, 2, 1, path)
            self._expect_kind(inputs, 0, "intArray", path)
            self._expect_int_width(inputs, 1, 32, path)
            array_type = self._type_at(inputs, 0)
            if array_type is not None:
                self._expect_int_width(outputs, 0, array_type.width or 0, path)
        elif kind == "setIndex":
            self._expect_arity(inputs, outputs, 3, 1, path)
            self._expect_kind(inputs, 0, "intArray", path)
            self._expect_int_width(inputs, 1, 32, path)
            self._expect_kind(inputs, 2, "int", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        elif kind == "length":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "intArray", path)
            self._expect_int_width(outputs, 0, 32, path)
        elif kind == "create":
            self._expect_arity(inputs, outputs, None, 1, path)
            self._expect_kind(outputs, 0, "intArray", path)
            self._check_created_array(inputs, outputs, "int", "intArray", path)
        else:
            self.module._error(path, f"unknown integer array operation {kind!r}")

    def _check_float_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind in _FLOAT_CONST_PRECISIONS:
            self._expect_arity(inputs, outputs, 0, 1, path)
            self._expect_float_precision(
                outputs, 0, _FLOAT_CONST_PRECISIONS[kind], path
            )
        elif kind in _FLOAT_BINARY_SAME:
            self._check_same_numeric_op(inputs, outputs, "float", False, path)
        elif kind in _FLOAT_BINARY_BOOL:
            self._check_same_numeric_op(inputs, outputs, "float", True, path)
        elif kind in _FLOAT_UNARY_SAME:
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "float", path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        elif kind in _FLOAT_UNARY_BOOL:
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "float", path)
            self._expect_int_width(outputs, 0, 1, path)
        else:
            self.module._error(path, f"unknown float operation {kind!r}")

    def _check_float_array_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind in _FLOAT_ARRAY_CONST_PRECISIONS:
            self._expect_arity(inputs, outputs, 0, 1, path)
            self._expect_array_precision(
                outputs, 0, "floatArray", _FLOAT_ARRAY_CONST_PRECISIONS[kind], path
            )
            self._expect_static_length(outputs, 0, len(getattr(op, kind)), path)
        elif kind == "zero":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_int_width(inputs, 0, 32, path)
            self._expect_array_precision(
                outputs, 0, "floatArray", _precision(op.zero), path
            )
        elif kind == "getIndex":
            self._expect_arity(inputs, outputs, 2, 1, path)
            self._expect_kind(inputs, 0, "floatArray", path)
            self._expect_int_width(inputs, 1, 32, path)
            array_type = self._type_at(inputs, 0)
            if array_type is not None:
                self._expect_float_precision(
                    outputs, 0, array_type.precision or 0, path
                )
        elif kind == "setIndex":
            self._expect_arity(inputs, outputs, 3, 1, path)
            self._expect_kind(inputs, 0, "floatArray", path)
            self._expect_int_width(inputs, 1, 32, path)
            array_type = self._type_at(inputs, 0)
            if array_type is not None:
                self._expect_float_precision(inputs, 2, array_type.precision or 0, path)
            self._expect_same_type(inputs, 0, outputs, 0, path)
        elif kind == "length":
            self._expect_arity(inputs, outputs, 1, 1, path)
            self._expect_kind(inputs, 0, "floatArray", path)
            self._expect_int_width(outputs, 0, 32, path)
        elif kind == "create":
            self._expect_arity(inputs, outputs, None, 1, path)
            self._expect_kind(outputs, 0, "floatArray", path)
            self._check_created_array(inputs, outputs, "float", "floatArray", path)
        else:
            self.module._error(path, f"unknown float array operation {kind!r}")

    def _check_scf_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        kind = str(op.which)
        if kind == "switch":
            self._check_switch(op.switch, inputs, outputs, path)
        elif kind == "for":
            self._check_for(getattr(op, "for"), inputs, outputs, path)
        elif kind == "while":
            self._check_while(getattr(op, "while"), inputs, outputs, path)
        elif kind == "doWhile":
            self._check_do_while(op.doWhile, inputs, outputs, path)
        else:
            self.module._error(path, f"unknown scf operation {kind!r}")

    def _check_switch(
        self, switch: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        self._expect_kind(inputs, 0, "int", path)
        branches = list(switch.branches)
        default = switch.default
        has_default = self._region_has_content(default)

        regions = branches + ([default] if has_default else [])
        if not regions:
            self.module._error(
                path, "switch must contain at least one branch or default"
            )
            return

        source_types, target_types = self._region_signature(regions[0])
        for index, branch in enumerate(branches):
            self._expect_region_signature(
                branch, source_types, target_types, f"{path}.switch.branches[{index}]"
            )
            self.check_region(branch, f"{path}.switch.branches[{index}]")
        if has_default:
            self._expect_region_signature(
                default, source_types, target_types, f"{path}.switch.default"
            )
            self.check_region(default, f"{path}.switch.default")

        self._expect_signature(inputs[1:], source_types, f"{path}.inputs")
        self._expect_signature(outputs, target_types, f"{path}.outputs")

    def _check_for(
        self, region: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        if len(inputs) < 3:
            self.module._error(path, "for operation expects at least 3 inputs")
            return

        self._expect_kind(inputs, 0, "int", path)
        self._expect_same_type(inputs, 0, inputs, 1, path)
        self._expect_same_type(inputs, 0, inputs, 2, path)
        state_types = self._types(inputs[3:])
        self._expect_signature(outputs, state_types, f"{path}.outputs")
        iterator_and_state = [self._type_at(inputs, 0), *state_types]
        self._expect_region_signature(
            region, iterator_and_state, state_types, f"{path}.for"
        )
        self.check_region(region, f"{path}.for")

    def _check_while(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        state_types = self._types(inputs)
        self._expect_signature(outputs, state_types, f"{path}.outputs")
        self._expect_region_signature(
            op.condition,
            state_types,
            [_Type("int", width=1)],
            f"{path}.while.condition",
        )
        self._expect_region_signature(
            op.body, state_types, state_types, f"{path}.while.body"
        )
        self.check_region(op.condition, f"{path}.while.condition")
        self.check_region(op.body, f"{path}.while.body")

    def _check_do_while(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        state_types = self._types(inputs)
        self._expect_signature(outputs, state_types, f"{path}.outputs")
        self._expect_region_signature(
            op.body, state_types, state_types, f"{path}.doWhile.body"
        )
        self._expect_region_signature(
            op.condition,
            state_types,
            [_Type("int", width=1)],
            f"{path}.doWhile.condition",
        )
        self.check_region(op.body, f"{path}.doWhile.body")
        self.check_region(op.condition, f"{path}.doWhile.condition")

    def _check_func_op(
        self, op: Any, inputs: list[int], outputs: list[int], path: str
    ) -> None:
        function_index = int(op.funcCall)
        signature = self.module.function_signature(function_index)
        if signature is None:
            self.module._error(path, f"function index {function_index} is out of range")
            return
        input_types, output_types = signature
        self._expect_signature(inputs, input_types, f"{path}.inputs")
        self._expect_signature(outputs, output_types, f"{path}.outputs")

    def _check_same_numeric_op(
        self,
        inputs: list[int],
        outputs: list[int],
        kind: str,
        bool_output: bool,
        path: str,
    ) -> None:
        self._expect_arity(inputs, outputs, 2, 1, path)
        self._expect_kind(inputs, 0, kind, path)
        self._expect_same_type(inputs, 0, inputs, 1, path)
        if bool_output:
            self._expect_int_width(outputs, 0, 1, path)
        else:
            self._expect_same_type(inputs, 0, outputs, 0, path)

    def _check_created_array(
        self,
        inputs: list[int],
        outputs: list[int],
        scalar_kind: str,
        array_kind: str,
        path: str,
    ) -> None:
        for index in range(len(inputs)):
            self._expect_kind(inputs, index, scalar_kind, path)

        output_type = self._type_at(outputs, 0)
        if output_type is None or output_type.kind != array_kind or not inputs:
            return

        first_type = self._type_at(inputs, 0)
        if first_type is None:
            return

        for index in range(1, len(inputs)):
            self._expect_same_type(inputs, 0, inputs, index, path)

        if scalar_kind == "int":
            expected = first_type.width
            actual = output_type.width
        else:
            expected = first_type.precision
            actual = output_type.precision
        if expected != actual:
            self.module._error(
                f"{path}.outputs",
                f"array output uses {actual}, expected {expected}",
            )
        self._expect_static_length(outputs, 0, len(inputs), path)

    def _expect_arity(
        self,
        inputs: list[int],
        outputs: list[int],
        expected_inputs: int | None,
        expected_outputs: int | None,
        path: str,
    ) -> None:
        if expected_inputs is not None and len(inputs) != expected_inputs:
            self.module._error(
                f"{path}.inputs",
                f"expected {expected_inputs} inputs, got {len(inputs)}",
            )
        if expected_outputs is not None and len(outputs) != expected_outputs:
            self.module._error(
                f"{path}.outputs",
                f"expected {expected_outputs} outputs, got {len(outputs)}",
            )

    def _expect_kind(self, values: list[int], index: int, kind: str, path: str) -> None:
        type_ = self._type_at(values, index)
        if type_ is not None and type_.kind != kind:
            self.module._error(
                path,
                f"value {values[index]} has type {_format_type(type_)}, expected {kind}",
            )

    def _expect_int_width(
        self, values: list[int], index: int, width: int, path: str
    ) -> None:
        type_ = self._type_at(values, index)
        expected = _Type("int", width=width)
        if type_ is not None and type_ != expected:
            self.module._error(
                path,
                f"value {values[index]} has type {_format_type(type_)}, expected {_format_type(expected)}",
            )

    def _expect_float_precision(
        self, values: list[int], index: int, precision: int, path: str
    ) -> None:
        type_ = self._type_at(values, index)
        expected = _Type("float", precision=precision)
        if type_ is not None and type_ != expected:
            self.module._error(
                path,
                f"value {values[index]} has type {_format_type(type_)}, expected {_format_type(expected)}",
            )

    def _expect_array_width(
        self, values: list[int], index: int, kind: str, width: int, path: str
    ) -> None:
        type_ = self._type_at(values, index)
        if type_ is not None and (type_.kind != kind or type_.width != width):
            self.module._error(
                path,
                f"value {values[index]} has type {_format_type(type_)}, expected {kind}({width})",
            )

    def _expect_array_precision(
        self, values: list[int], index: int, kind: str, precision: int, path: str
    ) -> None:
        type_ = self._type_at(values, index)
        if type_ is not None and (type_.kind != kind or type_.precision != precision):
            self.module._error(
                path,
                f"value {values[index]} has type {_format_type(type_)}, expected {kind}({precision})",
            )

    def _expect_static_length(
        self, values: list[int], index: int, length: int, path: str
    ) -> None:
        type_ = self._type_at(values, index)
        if type_ is not None and type_.length is not None and type_.length != length:
            self.module._error(
                path,
                f"value {values[index]} has length {type_.length}, expected {length}",
            )

    def _expect_same_type(
        self,
        left_values: list[int],
        left_index: int,
        right_values: list[int],
        right_index: int,
        path: str,
    ) -> None:
        left = self._type_at(left_values, left_index)
        right = self._type_at(right_values, right_index)
        if left is not None and right is not None and left != right:
            self.module._error(
                path,
                f"value {right_values[right_index]} has type {_format_type(right)}, "
                f"expected {_format_type(left)} from value {left_values[left_index]}",
            )

    def _expect_signature(
        self, values: list[int], expected: list[_Type | None], path: str
    ) -> None:
        if len(values) != len(expected):
            self.module._error(
                path,
                f"expected {len(expected)} values, got {len(values)}",
            )
            return
        for index, expected_type in enumerate(expected):
            actual = self._type(values[index])
            if expected_type is not None and not _same_type(actual, expected_type):
                self.module._error(
                    path,
                    f"value {values[index]} has type {_format_type(actual)}, "
                    f"expected {_format_type(expected_type)}",
                )

    def _expect_region_signature(
        self,
        region: Any,
        expected_sources: list[_Type | None],
        expected_targets: list[_Type | None],
        path: str,
    ) -> None:
        sources, targets = self._region_signature(region)
        if sources != expected_sources:
            self.module._error(
                f"{path}.sources",
                f"region source signature is {self._format_signature(sources)}, "
                f"expected {self._format_signature(expected_sources)}",
            )
        if targets != expected_targets:
            self.module._error(
                f"{path}.targets",
                f"region target signature is {self._format_signature(targets)}, "
                f"expected {self._format_signature(expected_targets)}",
            )

    def _region_signature(
        self, region: Any
    ) -> tuple[list[_Type | None], list[_Type | None]]:
        return self._types([int(value) for value in region.sources]), self._types(
            [int(value) for value in region.targets]
        )

    def _region_has_content(self, region: Any) -> bool:
        return (
            len(region.sources) > 0
            or len(region.targets) > 0
            or len(region.operations) > 0
            or len(region.metadata) > 0
        )

    def _type_at(self, values: list[int], index: int) -> _Type | None:
        if index >= len(values):
            return None
        return self._type(values[index])

    def _format_signature(self, types: list[_Type | None]) -> str:
        return "(" + ", ".join(_format_type(type_) for type_ in types) + ")"
