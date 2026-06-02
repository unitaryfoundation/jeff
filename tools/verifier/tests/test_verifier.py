from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from jeff import schema
from tools.verifier import verify_module


InstructionBuilder = Callable[[Any], None]


def _set_type(value: Any, kind: str, param: int | None = None) -> None:
    if kind == "qubit":
        value.type.qubit = None
    elif kind == "qureg":
        qureg = value.type.init("qureg")
        if param is None:
            qureg.dynamic = None
        else:
            qureg.static = param
    elif kind == "int":
        assert param is not None
        value.type.int = param
    elif kind == "intArray":
        assert param is not None
        int_array = value.type.init("intArray")
        int_array.bitwidth = param
        int_array.length.dynamic = None
    elif kind == "float":
        assert param in {32, 64}
        value.type.float = f"float{param}"
    elif kind == "floatArray":
        assert param in {32, 64}
        float_array = value.type.init("floatArray")
        float_array.precision = f"float{param}"
        float_array.length.dynamic = None
    else:
        raise AssertionError(f"unknown test type {kind}")


def _init_indices(builder: Any, field: str, values: list[int]) -> None:
    items = builder.init(field, len(values))
    for index, value in enumerate(values):
        items[index] = value


def _module(
    types: list[tuple[str, int | None]],
    sources: list[int],
    targets: list[int],
    operations: int,
) -> Any:
    module = schema.Module.new_message()
    module.version = schema.schemaVersionMajor
    module.versionMinor = schema.schemaVersionMinor
    module.versionPatch = schema.schemaVersionPatch
    module.tool = "test"
    module.toolVersion = "0"

    strings = module.init("strings", 1)
    strings[0] = "main"

    functions = module.init("functions", 1)
    function = functions[0]
    function.name = 0
    definition = function.init("definition")

    values = definition.init("values", len(types))
    for index, (kind, param) in enumerate(types):
        _set_type(values[index], kind, param)

    _init_indices(definition.body, "sources", sources)
    _init_indices(definition.body, "targets", targets)
    definition.body.init("operations", operations)
    return module


def _op(
    module: Any,
    index: int,
    inputs: list[int],
    outputs: list[int],
    instruction: InstructionBuilder,
) -> None:
    op = module.functions[0].definition.body.operations[index]
    _init_indices(op, "inputs", inputs)
    _init_indices(op, "outputs", outputs)
    instruction(op.instruction)


def _int_const(width: int, value: int = 0) -> InstructionBuilder:
    def build(instruction: Any) -> None:
        int_op = instruction.init("int")
        if width == 1:
            int_op.const1 = bool(value)
        else:
            setattr(int_op, f"const{width}", value)

    return build


def _int_add(instruction: Any) -> None:
    instruction.init("int").add = None


def _float_const(precision: int, value: float = 0.0) -> InstructionBuilder:
    def build(instruction: Any) -> None:
        setattr(instruction.init("float"), f"const{precision}", value)

    return build


def _float_max(instruction: Any) -> None:
    instruction.init("float").max = None


def _qubit_reset(instruction: Any) -> None:
    instruction.init("qubit").reset = None


def _switch_with_branch(
    branch_sources: list[int],
    branch_targets: list[int],
) -> InstructionBuilder:
    def build(instruction: Any) -> None:
        switch = instruction.init("scf").init("switch")
        branches = switch.init("branches", 1)
        _init_indices(branches[0], "sources", branch_sources)
        _init_indices(branches[0], "targets", branch_targets)
        branches[0].init("operations", 0)

    return build


def _messages(module: Any) -> list[str]:
    return [error.message for error in verify_module(module.as_reader())]


def test_valid_module_has_required_attributes() -> None:
    module = _module([("int", 32)], [], [0], 1)
    _op(module, 0, [], [0], _int_const(32))

    assert verify_module(module.as_reader()) == []


def test_missing_required_module_attributes_are_reported() -> None:
    module = schema.Module.new_message()
    module.version = schema.schemaVersionMajor
    module.versionMinor = schema.schemaVersionMinor
    module.versionPatch = schema.schemaVersionPatch

    assert "module must contain at least one function" in _messages(module)


def test_values_can_be_used_after_definition() -> None:
    module = _module([("int", 32), ("int", 32), ("int", 32)], [], [2], 3)
    _op(module, 0, [], [0], _int_const(32))
    _op(module, 1, [], [1], _int_const(32))
    _op(module, 2, [0, 1], [2], _int_add)

    assert verify_module(module.as_reader()) == []


def test_value_used_before_definition_is_reported() -> None:
    module = _module([("int", 32), ("int", 32), ("int", 32)], [], [2], 1)
    _op(module, 0, [0, 1], [2], _int_add)

    assert any("used before it is defined" in message for message in _messages(module))


def test_values_used_in_body_must_exist_in_value_table() -> None:
    module = _module([("int", 32)], [], [], 1)
    _op(module, 0, [], [1], _int_const(32))

    assert "value index 1 is out of range" in _messages(module)


def test_operation_inputs_and_outputs_have_expected_types() -> None:
    module = _module([("qubit", None), ("qubit", None)], [0], [1], 1)
    _op(module, 0, [0], [1], _qubit_reset)

    assert verify_module(module.as_reader()) == []


def test_unexpected_operation_type_is_reported() -> None:
    module = _module([("int", 32), ("qubit", None)], [0], [1], 1)
    _op(module, 0, [0], [1], _qubit_reset)

    assert any("expected qubit" in message for message in _messages(module))


def test_integer_operations_require_matching_bitwidths() -> None:
    module = _module([("int", 32), ("int", 32), ("int", 32)], [], [2], 3)
    _op(module, 0, [], [0], _int_const(32))
    _op(module, 1, [], [1], _int_const(32))
    _op(module, 2, [0, 1], [2], _int_add)

    assert verify_module(module.as_reader()) == []


def test_integer_bitwidth_mismatch_is_reported() -> None:
    module = _module([("int", 32), ("int", 64), ("int", 32)], [], [2], 3)
    _op(module, 0, [], [0], _int_const(32))
    _op(module, 1, [], [1], _int_const(64))
    _op(module, 2, [0, 1], [2], _int_add)

    assert any("expected int(32)" in message for message in _messages(module))


def test_float_operations_require_matching_precisions() -> None:
    module = _module([("float", 64), ("float", 64), ("float", 64)], [], [2], 3)
    _op(module, 0, [], [0], _float_const(64))
    _op(module, 1, [], [1], _float_const(64))
    _op(module, 2, [0, 1], [2], _float_max)

    assert verify_module(module.as_reader()) == []


def test_float_precision_mismatch_is_reported() -> None:
    module = _module([("float", 64), ("float", 32), ("float", 64)], [], [2], 3)
    _op(module, 0, [], [0], _float_const(64))
    _op(module, 1, [], [1], _float_const(32))
    _op(module, 2, [0, 1], [2], _float_max)

    assert any("expected float(64)" in message for message in _messages(module))


def test_linear_qubit_can_be_used_exactly_once() -> None:
    module = _module([("qubit", None), ("qubit", None)], [0], [1], 1)
    _op(module, 0, [0], [1], _qubit_reset)

    assert verify_module(module.as_reader()) == []


def test_linear_qubit_used_twice_is_reported() -> None:
    module = _module(
        [("qubit", None), ("qubit", None), ("qubit", None)], [0], [1, 2], 2
    )
    _op(module, 0, [0], [1], _qubit_reset)
    _op(module, 1, [0], [2], _qubit_reset)

    assert any("used 2 times" in message for message in _messages(module))


def test_regions_can_use_values_through_sources() -> None:
    module = _module(
        [("int", 32), ("int", 32), ("int", 32), ("int", 32)],
        [0, 1],
        [2],
        1,
    )
    _op(module, 0, [0, 1], [2], _switch_with_branch([3], [3]))

    assert verify_module(module.as_reader()) == []


def test_region_references_from_above_are_reported() -> None:
    module = _module(
        [("int", 32), ("int", 32), ("int", 32), ("int", 32)],
        [0, 1],
        [2],
        1,
    )
    _op(module, 0, [0, 1], [2], _switch_with_branch([3], [1]))

    assert any("escapes into the region" in message for message in _messages(module))
