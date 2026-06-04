from __future__ import annotations

import jeff

from tools.verifier.jeff_verifier import verify_module

SCHEMA_VERSION = (
    int(jeff.schema.schemaVersionMajor),
    int(jeff.schema.schemaVersionMinor),
    int(jeff.schema.schemaVersionPatch),
)


def test_required_module_attributes_are_checked() -> None:
    _assert_ok(_empty_module())
    _assert_error(_empty_module(version=(0, 0, 0)), "module version")
    _assert_error(_empty_module(entrypoint=1), "entrypoint 1")


def test_values_must_be_defined_before_use() -> None:
    _assert_ok(_int_add_module())
    module = _module_from_parts(
        [("int", 32), ("int", 32)],
        sources=[],
        targets=[1],
        ops=[_op("int", "not", [0], [1])],
    )
    _assert_error(module, "used before it is defined")


def test_body_references_must_exist_in_value_table() -> None:
    _assert_ok(_int_add_module())
    module = _module_from_parts(
        [("int", 32)],
        sources=[],
        targets=[0],
        ops=[_op("int", "not", [2], [0])],
    )
    _assert_error(module, "outside this function's value table")


def test_operation_inputs_and_outputs_must_have_expected_types() -> None:
    _assert_ok(
        _module_from_parts(
            [("int", 32), ("int", 32)],
            sources=[0],
            targets=[1],
            ops=[_op("int", "not", [0], [1])],
        )
    )
    module = _module_from_parts(
        [("float", 32), ("float", 32)],
        sources=[0],
        targets=[1],
        ops=[_op("int", "not", [0], [1])],
    )
    _assert_error(module, "expected int")


def test_integer_and_float_ops_require_matching_width_or_precision() -> None:
    _assert_ok(_int_add_module())
    bad_int = _module_from_parts(
        [("int", 32), ("int", 64), ("int", 32)],
        sources=[0, 1],
        targets=[2],
        ops=[_op("int", "add", [0, 1], [2])],
    )
    _assert_error(bad_int, "must all have the same type")

    _assert_ok(
        _module_from_parts(
            [("float", 32), ("float", 32), ("float", 32)],
            sources=[0, 1],
            targets=[2],
            ops=[_op("float", "max", [0, 1], [2])],
        )
    )
    bad_float = _module_from_parts(
        [("float", 32), ("float", 64), ("float", 32)],
        sources=[0, 1],
        targets=[2],
        ops=[_op("float", "max", [0, 1], [2])],
    )
    _assert_error(bad_float, "must all have the same type")


def test_quantum_values_are_linear() -> None:
    _assert_ok(
        _module_from_parts(
            [("qubit",)],
            sources=[],
            targets=[],
            ops=[
                _op("qubit", "alloc", [], [0]),
                _op("qubit", "free", [0], []),
            ],
        )
    )
    module = _module_from_parts(
        [("qubit",)],
        sources=[],
        targets=[],
        ops=[_op("qubit", "alloc", [], [0])],
    )
    _assert_error(module, "expected exactly 1")


def test_nested_regions_are_isolated_from_parent_scope() -> None:
    _assert_ok(_switch_module(branch_uses_parent=False))
    module = _switch_module(branch_uses_parent=True)
    _assert_error(module, "not isolated from above")


def _assert_ok(module: object) -> None:
    result = verify_module(module)
    assert result.ok, [error.message for error in result.errors]


def _assert_error(module: object, expected: str) -> None:
    result = verify_module(module)
    messages = "\n".join(error.message for error in result.errors)
    assert not result.ok
    assert expected in messages


def _empty_module(
    *, version: tuple[int, int, int] = SCHEMA_VERSION, entrypoint: int = 0
) -> object:
    return _module_from_parts(
        [],
        sources=[],
        targets=[],
        ops=[],
        version=version,
        entrypoint=entrypoint,
    )


def _int_add_module() -> object:
    return _module_from_parts(
        [("int", 32), ("int", 32), ("int", 32)],
        sources=[],
        targets=[2],
        ops=[
            _op("int", "const32", [], [0], 1),
            _op("int", "const32", [], [1], 2),
            _op("int", "add", [0, 1], [2]),
        ],
    )


def _switch_module(*, branch_uses_parent: bool) -> object:
    branch_input = 1 if branch_uses_parent else 2
    branch = _region(
        sources=[2],
        targets=[3],
        ops=[_op("int", "not", [branch_input], [3])],
    )
    return _module_from_parts(
        [
            ("int", 32),
            ("int", 32),
            ("int", 32),
            ("int", 32),
            ("int", 32),
        ],
        sources=[0, 1],
        targets=[4],
        ops=[_op("scf", "switch", [0, 1], [4], branches=[branch])],
    )


def _module_from_parts(
    type_specs: list[tuple[object, ...]],
    *,
    sources: list[int],
    targets: list[int],
    ops: list[dict[str, object]],
    version: tuple[int, int, int] = SCHEMA_VERSION,
    entrypoint: int = 0,
) -> object:
    module = jeff.schema.Module.new_message()
    module.version = version[0]
    module.versionMinor = version[1]
    module.versionPatch = version[2]
    module.entrypoint = entrypoint

    strings = module.init("strings", 1)
    strings[0] = "main"

    functions = module.init("functions", 1)
    function = functions[0]
    function.name = 0
    definition = function.init("definition")

    values = definition.init("values", len(type_specs))
    for index, type_spec in enumerate(type_specs):
        _write_type(values[index].type, type_spec)

    _write_region(definition.body, _region(sources, targets, ops))
    return jeff.JeffModule.from_encoding(module.as_reader())


def _region(
    sources: list[int], targets: list[int], ops: list[dict[str, object]]
) -> dict[str, object]:
    return {"sources": sources, "targets": targets, "ops": ops}


def _op(
    kind: str,
    subkind: str,
    inputs: list[int],
    outputs: list[int],
    data: object = None,
    *,
    branches: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "kind": kind,
        "subkind": subkind,
        "inputs": inputs,
        "outputs": outputs,
        "data": data,
        "branches": branches or [],
    }


def _write_region(builder: object, region: dict[str, object]) -> None:
    sources = region["sources"]
    source_list = builder.init("sources", len(sources))
    for index, value in enumerate(sources):
        source_list[index] = value

    targets = region["targets"]
    target_list = builder.init("targets", len(targets))
    for index, value in enumerate(targets):
        target_list[index] = value

    ops = region["ops"]
    op_list = builder.init("operations", len(ops))
    for index, op in enumerate(ops):
        _write_op(op_list[index], op)


def _write_op(builder: object, op: dict[str, object]) -> None:
    inputs = op["inputs"]
    input_list = builder.init("inputs", len(inputs))
    for index, value in enumerate(inputs):
        input_list[index] = value

    outputs = op["outputs"]
    output_list = builder.init("outputs", len(outputs))
    for index, value in enumerate(outputs):
        output_list[index] = value

    kind = op["kind"]
    subkind = op["subkind"]
    if kind == "scf" and subkind == "switch":
        scf = builder.instruction.init("scf")
        switch = scf.init("switch")
        branches = op["branches"]
        branch_list = switch.init("branches", len(branches))
        for index, branch in enumerate(branches):
            _write_region(branch_list[index], branch)
        return

    instruction = builder.instruction.init(kind)
    setattr(instruction, subkind, op["data"])


def _write_type(builder: object, type_spec: tuple[object, ...]) -> None:
    kind = type_spec[0]
    if kind == "qubit":
        builder.qubit = None
    elif kind == "qureg":
        builder.init("qureg").dynamic = None
    elif kind == "int":
        builder.int = type_spec[1]
    elif kind == "float":
        builder.float = f"float{type_spec[1]}"
    else:
        raise AssertionError(f"unsupported test type: {type_spec!r}")
