from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import jeff


@dataclass(frozen=True)
class VerificationError:
    """A verifier diagnostic with a stable location string."""

    location: str
    message: str


@dataclass(frozen=True)
class VerificationResult:
    """Result returned by the verifier."""

    errors: list[VerificationError]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class TypeRef:
    kind: str
    bitwidth: int | None = None
    length: int | None = None


@dataclass(frozen=True)
class FunctionSignature:
    inputs: tuple[TypeRef, ...]
    outputs: tuple[TypeRef, ...]


QUBIT = TypeRef("qubit")
QUREG = TypeRef("qureg")
INT1 = TypeRef("int", 1)
INT32 = TypeRef("int", 32)
ANY_INT = TypeRef("int")
ANY_FLOAT = TypeRef("float")
ANY_INT_ARRAY = TypeRef("intArray")
ANY_FLOAT_ARRAY = TypeRef("floatArray")

WELL_KNOWN_GATES = {
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

INT_CONSTANTS = {
    "const1": 1,
    "const8": 8,
    "const16": 16,
    "const32": 32,
    "const64": 64,
}
INT_BINARY_SAME = {
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
INT_COMPARISONS = {"eq", "ltS", "lteS", "ltU", "lteU"}
INT_UNARY_SAME = {"not", "abs"}

FLOAT_CONSTANTS = {"const32": 32, "const64": 64}
FLOAT_BINARY_SAME = {"add", "sub", "mul", "pow", "atan2", "max", "min"}
FLOAT_COMPARISONS = {"eq", "lt", "lte"}
FLOAT_UNARY_SAME = {
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
FLOAT_UNARY_BOOL = {"isNan", "isInf"}


class _Verifier:
    def __init__(self) -> None:
        self.errors: list[VerificationError] = []
        self.function_signatures: list[FunctionSignature | None] = []

    def verify_module(self, module: object) -> VerificationResult:
        data = getattr(module, "_raw_data", module)
        functions = list(data.functions)
        self._verify_module_attributes(data, functions)
        self.function_signatures = self._collect_function_signatures(functions)
        self._verify_function_names(data, functions)

        for index, func in enumerate(functions):
            loc = f"module.functions[{index}]"
            func_kind = _which(func)
            if func_kind == "definition":
                self._verify_function_definition(func, loc)
            elif func_kind == "declaration":
                self._verify_function_declaration(func, loc)
            else:
                self._error(loc, f"unsupported function kind {func_kind!r}")

        return VerificationResult(self.errors)

    def _verify_module_attributes(
        self, module: object, functions: Sequence[object]
    ) -> None:
        expected = (
            int(jeff.schema.schemaVersionMajor),
            int(jeff.schema.schemaVersionMinor),
            int(jeff.schema.schemaVersionPatch),
        )
        actual = (
            int(module.version),
            int(module.versionMinor),
            int(module.versionPatch),
        )
        if actual != expected:
            self._error(
                "module.version",
                f"module version {_format_version(actual)} does not match "
                f"schema version {_format_version(expected)}",
            )

        entrypoint = int(module.entrypoint)
        if not functions:
            self._error("module.functions", "module must define at least one function")
        elif entrypoint < 0 or entrypoint >= len(functions):
            self._error(
                "module.entrypoint",
                f"entrypoint {entrypoint} is outside the functions list",
            )
        elif _which(functions[entrypoint]) != "definition":
            self._error("module.entrypoint", "entrypoint must refer to a definition")

    def _verify_function_names(
        self, module: object, functions: Sequence[object]
    ) -> None:
        strings = list(module.strings)
        seen: dict[str, int] = {}
        for index, func in enumerate(functions):
            loc = f"module.functions[{index}].name"
            name_index = int(func.name)
            if name_index >= len(strings):
                self._error(
                    loc,
                    f"function name index {name_index} is outside the string table",
                )
                continue

            name = str(strings[name_index])
            if name in seen:
                self._error(
                    loc,
                    f"function name {name!r} duplicates function {seen[name]}",
                )
            seen[name] = index

    def _collect_function_signatures(
        self, functions: Sequence[object]
    ) -> list[FunctionSignature | None]:
        signatures: list[FunctionSignature | None] = []
        for func in functions:
            func_kind = _which(func)
            if func_kind == "definition":
                definition = func.definition
                types = [_type_from_value(value) for value in definition.values]
                inputs = _types_for_indices(definition.body.sources, types)
                outputs = _types_for_indices(definition.body.targets, types)
            elif func_kind == "declaration":
                inputs = tuple(
                    _type_from_value(value) for value in func.declaration.inputs
                )
                outputs = tuple(
                    _type_from_value(value) for value in func.declaration.outputs
                )
            else:
                signatures.append(None)
                continue

            if inputs is None or outputs is None:
                signatures.append(None)
            else:
                signatures.append(FunctionSignature(inputs, outputs))
        return signatures

    def _verify_function_definition(self, func: object, loc: str) -> None:
        definition = func.definition
        types = [_type_from_value(value) for value in definition.values]
        self._verify_region(definition.body, types, f"{loc}.body", set())

    def _verify_function_declaration(self, func: object, loc: str) -> None:
        for index, value in enumerate(func.declaration.inputs):
            _type_from_value(value)
            self._check_metadata_indices(value, f"{loc}.inputs[{index}]")
        for index, value in enumerate(func.declaration.outputs):
            _type_from_value(value)
            self._check_metadata_indices(value, f"{loc}.outputs[{index}]")

    def _verify_region(
        self,
        region: object,
        types: Sequence[TypeRef],
        loc: str,
        parent_visible: set[int],
    ) -> None:
        sources = _indices(region.sources)
        targets = _indices(region.targets)
        operations = list(region.operations)

        valid_sources = [
            index
            for pos, index in enumerate(sources)
            if self._check_value_index(index, types, f"{loc}.sources[{pos}]")
        ]

        definition_counts = Counter(valid_sources)
        for op_index, op in enumerate(operations):
            for out_pos, index in enumerate(_indices(op.outputs)):
                out_loc = f"{loc}.operations[{op_index}].outputs[{out_pos}]"
                if self._check_value_index(index, types, out_loc):
                    definition_counts[index] += 1

        definitions = set(definition_counts)
        for index, count in definition_counts.items():
            if count > 1:
                self._error(
                    loc,
                    f"value %{index} is defined {count} times in this region",
                )

        for op_index, op in enumerate(operations):
            op_loc = f"{loc}.operations[{op_index}]"
            for in_pos, index in enumerate(_indices(op.inputs)):
                in_loc = f"{op_loc}.inputs[{in_pos}]"
                if self._check_value_index(index, types, in_loc):
                    self._check_region_use(index, definitions, parent_visible, in_loc)
            self._verify_op_types(op, types, op_loc)

        for target_pos, index in enumerate(targets):
            target_loc = f"{loc}.targets[{target_pos}]"
            if self._check_value_index(index, types, target_loc):
                self._check_region_use(index, definitions, parent_visible, target_loc)

        self._verify_linearity(region, types, definitions, loc)

        visible_above = parent_visible | definitions
        for op_index, op in enumerate(operations):
            for name, nested in self._nested_regions(op):
                nested_loc = f"{loc}.operations[{op_index}].{name}"
                self._verify_region(nested, types, nested_loc, visible_above)

    def _check_region_use(
        self,
        index: int,
        definitions: set[int],
        parent_visible: set[int],
        loc: str,
    ) -> None:
        if index in definitions:
            return

        self._error(loc, f"value %{index} is used before it is defined in this region")
        if index in parent_visible:
            self._error(
                loc,
                f"region is not isolated from above; value %{index} is captured "
                "from a parent region",
            )

    def _verify_linearity(
        self,
        region: object,
        types: Sequence[TypeRef],
        definitions: set[int],
        loc: str,
    ) -> None:
        uses: Counter[int] = Counter()
        for op in region.operations:
            for index in _indices(op.inputs):
                if _valid_index(index, types) and _is_quantum(types[index]):
                    uses[index] += 1
        for index in _indices(region.targets):
            if _valid_index(index, types) and _is_quantum(types[index]):
                uses[index] += 1

        for index in sorted(definitions):
            if _is_quantum(types[index]) and uses[index] != 1:
                self._error(
                    loc,
                    f"linear value %{index} has {uses[index]} uses; expected exactly 1",
                )

    def _verify_op_types(
        self, op: object, types: Sequence[TypeRef], loc: str) -> None:
        inputs = _lookup_types(_indices(op.inputs), types)
        outputs = _lookup_types(_indices(op.outputs), types)
        if inputs is None or outputs is None:
            return

        kind = _which(op.instruction)
        instruction = getattr(op.instruction, kind)
        subkind = _which(instruction)

        if kind == "qubit":
            self._verify_qubit_op(instruction, subkind, inputs, outputs, loc)
        elif kind == "qureg":
            self._verify_qureg_op(subkind, inputs, outputs, loc)
        elif kind == "int":
            self._verify_int_op(subkind, inputs, outputs, loc)
        elif kind == "intArray":
            self._verify_int_array_op(instruction, subkind, inputs, outputs, loc)
        elif kind == "float":
            self._verify_float_op(subkind, inputs, outputs, loc)
        elif kind == "floatArray":
            self._verify_float_array_op(instruction, subkind, inputs, outputs, loc)
        elif kind == "scf":
            self._verify_scf_op(instruction, subkind, inputs, outputs, loc)
        elif kind == "func":
            self._verify_func_op(instruction, inputs, outputs, loc)
        else:
            self._error(loc, f"unsupported operation kind {kind!r}")

    def _verify_qubit_op(
        self,
        instruction: object,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind == "alloc":
            self._expect_signature(loc, inputs, outputs, [], [QUBIT])
        elif subkind in {"free", "freeZero"}:
            self._expect_signature(loc, inputs, outputs, [QUBIT], [])
        elif subkind == "measure":
            self._expect_signature(loc, inputs, outputs, [QUBIT], [INT1])
        elif subkind == "measureNd":
            self._expect_signature(loc, inputs, outputs, [QUBIT], [QUBIT, INT1])
        elif subkind == "reset":
            self._expect_signature(loc, inputs, outputs, [QUBIT], [QUBIT])
        elif subkind == "gate":
            self._verify_qubit_gate(instruction.gate, inputs, outputs, loc)
        else:
            self._error(loc, f"unsupported qubit operation {subkind!r}")

    def _verify_qubit_gate(
        self,
        gate: object,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        gate_kind = _which(gate)
        controls = int(gate.controlQubits)
        if gate_kind == "wellKnown":
            gate_name = str(gate.wellKnown)
            if gate_name not in WELL_KNOWN_GATES:
                self._error(loc, f"unknown well-known gate {gate_name!r}")
                return
            qubits, params = WELL_KNOWN_GATES[gate_name]
        elif gate_kind == "ppr":
            qubits = len(gate.ppr.pauliString)
            params = 1
        elif gate_kind == "custom":
            qubits = int(gate.custom.numQubits)
            params = int(gate.custom.numParams)
        else:
            self._error(loc, f"unsupported gate kind {gate_kind!r}")
            return

        quantum_inputs = qubits + controls
        if not self._expect_count(loc, inputs, quantum_inputs + params, "inputs"):
            return
        self._expect_count(loc, outputs, quantum_inputs, "outputs")
        for pos, input_type in enumerate(inputs[:quantum_inputs]):
            self._expect_type(input_type, QUBIT, f"{loc}.inputs[{pos}]")
        for pos, input_type in enumerate(inputs[quantum_inputs:]):
            self._expect_type(input_type, ANY_FLOAT, f"{loc}.inputs[{quantum_inputs + pos}]")
        for pos, output_type in enumerate(outputs):
            self._expect_type(output_type, QUBIT, f"{loc}.outputs[{pos}]")

    def _verify_qureg_op(
        self,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind == "alloc":
            self._expect_signature(loc, inputs, outputs, [INT32], [QUREG])
        elif subkind in {"free", "freeZero"}:
            self._expect_signature(loc, inputs, outputs, [QUREG], [])
        elif subkind == "extractIndex":
            self._expect_signature(loc, inputs, outputs, [QUREG, INT32], [QUREG, QUBIT])
        elif subkind == "insertIndex":
            self._expect_signature(
                loc, inputs, outputs, [QUREG, INT32, QUBIT], [QUREG]
            )
        elif subkind == "extractSlice":
            self._expect_signature(
                loc, inputs, outputs, [QUREG, INT32, INT32], [QUREG, QUREG]
            )
        elif subkind == "insertSlice":
            self._expect_signature(loc, inputs, outputs, [QUREG, INT32, QUREG], [QUREG])
        elif subkind == "length":
            self._expect_signature(loc, inputs, outputs, [QUREG], [QUREG, INT32])
        elif subkind == "split":
            self._expect_signature(loc, inputs, outputs, [QUREG, INT32], [QUREG, QUREG])
        elif subkind == "join":
            self._expect_signature(loc, inputs, outputs, [QUREG, QUREG], [QUREG])
        elif subkind == "create":
            if not self._expect_count(loc, outputs, 1, "outputs"):
                return
            for pos, input_type in enumerate(inputs):
                self._expect_type(input_type, QUBIT, f"{loc}.inputs[{pos}]")
            self._expect_type(outputs[0], QUREG, f"{loc}.outputs[0]")
        else:
            self._error(loc, f"unsupported qureg operation {subkind!r}")

    def _verify_int_op(
        self,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind in INT_CONSTANTS:
            self._expect_signature(
                loc, inputs, outputs, [], [TypeRef("int", INT_CONSTANTS[subkind])]
            )
        elif subkind in INT_BINARY_SAME:
            if self._expect_signature(loc, inputs, outputs, [ANY_INT, ANY_INT], [ANY_INT]):
                self._expect_same_type([inputs[0], inputs[1], outputs[0]], loc)
        elif subkind in INT_COMPARISONS:
            if self._expect_signature(loc, inputs, outputs, [ANY_INT, ANY_INT], [INT1]):
                self._expect_same_type([inputs[0], inputs[1]], loc)
        elif subkind in INT_UNARY_SAME:
            if self._expect_signature(loc, inputs, outputs, [ANY_INT], [ANY_INT]):
                self._expect_same_type([inputs[0], outputs[0]], loc)
        else:
            self._error(loc, f"unsupported integer operation {subkind!r}")

    def _verify_int_array_op(
        self,
        instruction: object,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind in INT_CONSTANTS:
            expected = TypeRef("intArray", INT_CONSTANTS[subkind])
            self._expect_signature(loc, inputs, outputs, [], [expected])
        elif subkind == "zero":
            expected = TypeRef("intArray", int(instruction.zero))
            self._expect_signature(loc, inputs, outputs, [INT32], [expected])
        elif subkind == "getIndex":
            if self._expect_signature(loc, inputs, outputs, [ANY_INT_ARRAY, INT32], [ANY_INT]):
                self._expect_type(outputs[0], TypeRef("int", inputs[0].bitwidth), loc)
        elif subkind == "setIndex":
            expected_value = TypeRef("int", inputs[0].bitwidth) if inputs else ANY_INT
            self._expect_signature(
                loc, inputs, outputs, [ANY_INT_ARRAY, INT32, expected_value], [ANY_INT_ARRAY]
            )
        elif subkind == "length":
            self._expect_signature(loc, inputs, outputs, [ANY_INT_ARRAY], [INT32])
        elif subkind == "create":
            if not self._expect_count(loc, outputs, 1, "outputs"):
                return
            self._expect_type(outputs[0], ANY_INT_ARRAY, f"{loc}.outputs[0]")
            for pos, input_type in enumerate(inputs):
                self._expect_type(input_type, ANY_INT, f"{loc}.inputs[{pos}]")
                if input_type.bitwidth != outputs[0].bitwidth:
                    self._error(
                        f"{loc}.inputs[{pos}]",
                        "array element bitwidth must match output array bitwidth",
                    )
        else:
            self._error(loc, f"unsupported integer-array operation {subkind!r}")

    def _verify_float_op(
        self,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind in FLOAT_CONSTANTS:
            self._expect_signature(
                loc, inputs, outputs, [], [TypeRef("float", FLOAT_CONSTANTS[subkind])]
            )
        elif subkind in FLOAT_BINARY_SAME:
            expected = [ANY_FLOAT, ANY_FLOAT]
            if self._expect_signature(loc, inputs, outputs, expected, [ANY_FLOAT]):
                self._expect_same_type([inputs[0], inputs[1], outputs[0]], loc)
        elif subkind in FLOAT_COMPARISONS:
            expected = [ANY_FLOAT, ANY_FLOAT]
            if self._expect_signature(loc, inputs, outputs, expected, [INT1]):
                self._expect_same_type([inputs[0], inputs[1]], loc)
        elif subkind in FLOAT_UNARY_SAME:
            if self._expect_signature(loc, inputs, outputs, [ANY_FLOAT], [ANY_FLOAT]):
                self._expect_same_type([inputs[0], outputs[0]], loc)
        elif subkind in FLOAT_UNARY_BOOL:
            self._expect_signature(loc, inputs, outputs, [ANY_FLOAT], [INT1])
        else:
            self._error(loc, f"unsupported float operation {subkind!r}")

    def _verify_float_array_op(
        self,
        instruction: object,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind in FLOAT_CONSTANTS:
            expected = TypeRef("floatArray", FLOAT_CONSTANTS[subkind])
            self._expect_signature(loc, inputs, outputs, [], [expected])
        elif subkind == "zero":
            expected = TypeRef("floatArray", _float_precision(instruction.zero))
            self._expect_signature(loc, inputs, outputs, [INT32], [expected])
        elif subkind == "getIndex":
            expected = [ANY_FLOAT_ARRAY, INT32]
            if self._expect_signature(loc, inputs, outputs, expected, [ANY_FLOAT]):
                self._expect_type(outputs[0], TypeRef("float", inputs[0].bitwidth), loc)
        elif subkind == "setIndex":
            expected_value = TypeRef("float", inputs[0].bitwidth) if inputs else ANY_FLOAT
            expected = [ANY_FLOAT_ARRAY, INT32, expected_value]
            self._expect_signature(loc, inputs, outputs, expected, [ANY_FLOAT_ARRAY])
        elif subkind == "length":
            self._expect_signature(loc, inputs, outputs, [ANY_FLOAT_ARRAY], [INT32])
        elif subkind == "create":
            if not self._expect_count(loc, outputs, 1, "outputs"):
                return
            self._expect_type(outputs[0], ANY_FLOAT_ARRAY, f"{loc}.outputs[0]")
            for pos, input_type in enumerate(inputs):
                self._expect_type(input_type, ANY_FLOAT, f"{loc}.inputs[{pos}]")
                if input_type.bitwidth != outputs[0].bitwidth:
                    self._error(
                        f"{loc}.inputs[{pos}]",
                        "array element precision must match output array precision",
                    )
        else:
            self._error(loc, f"unsupported float-array operation {subkind!r}")

    def _verify_scf_op(
        self,
        instruction: object,
        subkind: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if subkind == "switch":
            self._verify_switch_op(instruction.switch, inputs, outputs, loc)
        elif subkind == "for":
            body = getattr(instruction, "for")
            self._verify_for_op(body, inputs, outputs, loc)
        elif subkind == "while":
            while_op = getattr(instruction, "while")
            self._verify_while_like_op(while_op.condition, while_op.body, inputs, outputs, loc)
        elif subkind == "doWhile":
            self._verify_while_like_op(
                instruction.doWhile.condition,
                instruction.doWhile.body,
                inputs,
                outputs,
                loc,
            )
        else:
            self._error(loc, f"unsupported scf operation {subkind!r}")

    def _verify_switch_op(
        self,
        switch: object,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if not inputs:
            self._error(loc, "switch operation requires a selector input")
            return
        self._expect_type(inputs[0], ANY_INT, f"{loc}.inputs[0]")
        expected_sources = tuple(inputs[1:])
        expected_targets = tuple(outputs)
        branches = list(switch.branches)
        if not branches:
            self._error(loc, "switch operation requires at least one branch")
        for index, branch in enumerate(branches):
            self._expect_region_signature(
                branch,
                expected_sources,
                expected_targets,
                f"{loc}.branches[{index}]",
            )
        if _has_region(switch.default):
            self._expect_region_signature(
                switch.default,
                expected_sources,
                expected_targets,
                f"{loc}.default",
            )

    def _verify_for_op(
        self,
        body: object,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        if len(inputs) < 3:
            self._error(loc, "for operation requires start, stop, and step inputs")
            return
        for pos in range(3):
            self._expect_type(inputs[pos], ANY_INT, f"{loc}.inputs[{pos}]")
        self._expect_same_type([inputs[0], inputs[1], inputs[2]], loc)
        state = tuple(inputs[3:])
        if tuple(outputs) != state:
            self._error(loc, "for loop output state must match input state types")
        self._expect_region_signature(body, (inputs[0], *state), state, f"{loc}.body")

    def _verify_while_like_op(
        self,
        condition: object,
        body: object,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        state = tuple(inputs)
        if tuple(outputs) != state:
            self._error(loc, "loop output state must match input state types")
        self._expect_region_signature(condition, state, (INT1,), f"{loc}.condition")
        self._expect_region_signature(body, state, state, f"{loc}.body")

    def _verify_func_op(
        self,
        instruction: object,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        loc: str,
    ) -> None:
        func_index = int(instruction.funcCall)
        if func_index >= len(self.function_signatures):
            self._error(loc, f"function call index {func_index} is out of range")
            return
        signature = self.function_signatures[func_index]
        if signature is None:
            return
        if tuple(inputs) != signature.inputs:
            self._error(loc, "function call inputs do not match callee signature")
        if tuple(outputs) != signature.outputs:
            self._error(loc, "function call outputs do not match callee signature")

    def _nested_regions(self, op: object) -> Iterable[tuple[str, object]]:
        if _which(op.instruction) != "scf":
            return []

        scf = op.instruction.scf
        subkind = _which(scf)
        if subkind == "switch":
            nested: list[tuple[str, object]] = [
                (f"branches[{index}]", branch)
                for index, branch in enumerate(scf.switch.branches)
            ]
            if _has_region(scf.switch.default):
                nested.append(("default", scf.switch.default))
            return nested
        if subkind == "for":
            return [("body", getattr(scf, "for"))]
        if subkind == "while":
            while_op = getattr(scf, "while")
            return [("condition", while_op.condition), ("body", while_op.body)]
        if subkind == "doWhile":
            return [
                ("body", scf.doWhile.body),
                ("condition", scf.doWhile.condition),
            ]
        return []

    def _expect_region_signature(
        self,
        region: object,
        expected_sources: Sequence[TypeRef],
        expected_targets: Sequence[TypeRef],
        loc: str,
    ) -> None:
        source_types = _lookup_types(_indices(region.sources), self._current_types(region))
        target_types = _lookup_types(_indices(region.targets), self._current_types(region))
        if source_types is not None and tuple(source_types) != tuple(expected_sources):
            self._error(loc, "region source types do not match operation inputs")
        if target_types is not None and tuple(target_types) != tuple(expected_targets):
            self._error(loc, "region target types do not match operation outputs")

    def _current_types(self, _region: object) -> Sequence[TypeRef]:
        # The caller passes regions that belong to the function currently being
        # validated. This field is set immediately before checking op types.
        return self._active_types

    def _check_value_index(
        self, index: int, types: Sequence[TypeRef], loc: str
    ) -> bool:
        if not _valid_index(index, types):
            self._error(
                loc,
                f"value %{index} is outside this function's value table",
            )
            return False
        return True

    def _check_metadata_indices(self, _value: object, _loc: str) -> None:
        # Metadata payload validation is intentionally left out of this first
        # verifier. Cap'n Proto can hold arbitrary pointers in metadata values.
        return

    def _expect_signature(
        self,
        loc: str,
        inputs: Sequence[TypeRef],
        outputs: Sequence[TypeRef],
        expected_inputs: Sequence[TypeRef],
        expected_outputs: Sequence[TypeRef],
    ) -> bool:
        ok = True
        if not self._expect_count(loc, inputs, len(expected_inputs), "inputs"):
            ok = False
        if not self._expect_count(loc, outputs, len(expected_outputs), "outputs"):
            ok = False
        if not ok:
            return False

        for pos, (actual, expected) in enumerate(zip(inputs, expected_inputs)):
            ok = self._expect_type(actual, expected, f"{loc}.inputs[{pos}]") and ok
        for pos, (actual, expected) in enumerate(zip(outputs, expected_outputs)):
            ok = self._expect_type(actual, expected, f"{loc}.outputs[{pos}]") and ok
        return ok

    def _expect_count(
        self, loc: str, values: Sequence[TypeRef], expected: int, label: str
    ) -> bool:
        if len(values) == expected:
            return True
        self._error(loc, f"expected {expected} {label}, found {len(values)}")
        return False

    def _expect_type(self, actual: TypeRef, expected: TypeRef, loc: str) -> bool:
        if _matches(actual, expected):
            return True
        self._error(
            loc,
            f"expected {_format_type(expected)}, found {_format_type(actual)}",
        )
        return False

    def _expect_same_type(self, values: Sequence[TypeRef], loc: str) -> bool:
        if not values:
            return True
        first = values[0]
        for value in values[1:]:
            if value != first:
                self._error(
                    loc,
                    "integer or float operation operands/results must all have "
                    "the same type",
                )
                return False
        return True

    def _error(self, location: str, message: str) -> None:
        self.errors.append(VerificationError(location, message))


def verify_module(module: object) -> VerificationResult:
    """Verify a loaded ``jeff`` module or raw Cap'n Proto module reader."""

    verifier = _Verifier()
    return verifier.verify_module(module)


def verify_file(path: str | Path) -> VerificationResult:
    """Load and verify an encoded ``jeff`` module from disk."""

    return verify_module(jeff.load_module(path))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify encoded jeff modules")
    parser.add_argument("paths", nargs="+", help="encoded .jeff files to verify")
    args = parser.parse_args(argv)

    failed = False
    for raw_path in args.paths:
        path = Path(raw_path)
        result = verify_file(path)
        if result.ok:
            print(f"{path}: ok")
            continue

        failed = True
        for error in result.errors:
            print(f"{path}: {error.location}: {error.message}", file=sys.stderr)
    return 1 if failed else 0


def _which(value: object) -> str:
    which = getattr(value, "which")
    if callable(which):
        which = which()
    return str(which)


def _indices(values: Iterable[object]) -> list[int]:
    return [int(value) for value in values]


def _valid_index(index: int, types: Sequence[TypeRef]) -> bool:
    return 0 <= index < len(types)


def _lookup_types(
    indices: Sequence[int], types: Sequence[TypeRef]
) -> tuple[TypeRef, ...] | None:
    if any(not _valid_index(index, types) for index in indices):
        return None
    return tuple(types[index] for index in indices)


def _types_for_indices(
    indices: Iterable[object], types: Sequence[TypeRef]
) -> tuple[TypeRef, ...] | None:
    return _lookup_types(_indices(indices), types)


def _type_from_value(value: object) -> TypeRef:
    return _type_from_encoding(value.type)


def _type_from_encoding(type_data: object) -> TypeRef:
    kind = _which(type_data)
    if kind == "qubit":
        return TypeRef("qubit")
    if kind == "qureg":
        qureg = type_data.qureg
        length = int(qureg.static) if _which(qureg) == "static" else None
        return TypeRef("qureg", length=length)
    if kind == "int":
        return TypeRef("int", int(type_data.int))
    if kind == "intArray":
        array = type_data.intArray
        length = int(array.length.static) if _which(array.length) == "static" else None
        return TypeRef("intArray", int(array.bitwidth), length)
    if kind == "float":
        return TypeRef("float", _float_precision(type_data.float))
    if kind == "floatArray":
        array = type_data.floatArray
        length = int(array.length.static) if _which(array.length) == "static" else None
        return TypeRef("floatArray", _float_precision(array.precision), length)
    return TypeRef(kind)


def _float_precision(value: object) -> int:
    text = str(value)
    if text.endswith("32"):
        return 32
    if text.endswith("64"):
        return 64
    msg = f"unknown float precision {text!r}"
    raise ValueError(msg)


def _matches(actual: TypeRef, expected: TypeRef) -> bool:
    if actual.kind != expected.kind:
        return False
    if expected.bitwidth is not None and actual.bitwidth != expected.bitwidth:
        return False
    if expected.length is not None and actual.length != expected.length:
        return False
    return True


def _is_quantum(type_ref: TypeRef) -> bool:
    return type_ref.kind in {"qubit", "qureg"}


def _has_region(region: object) -> bool:
    try:
        if not region:
            return False
    except TypeError:
        pass
    return bool(region.sources or region.targets or region.operations)


def _format_type(type_ref: TypeRef) -> str:
    if type_ref.kind in {"int", "float"} and type_ref.bitwidth is not None:
        return f"{type_ref.kind}{type_ref.bitwidth}"
    if type_ref.kind in {"intArray", "floatArray"}:
        prefix = "int" if type_ref.kind == "intArray" else "float"
        width = "?" if type_ref.bitwidth is None else str(type_ref.bitwidth)
        length = "?" if type_ref.length is None else str(type_ref.length)
        return f"{prefix}{width}[{length}]"
    if type_ref.kind == "qureg":
        length = "?" if type_ref.length is None else str(type_ref.length)
        return f"qureg[{length}]"
    return type_ref.kind


def _format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)
