from pathlib import Path

from jeff import (
    CustomGate,
    FloatArrayType,
    FloatType,
    FunctionDecl,
    FunctionDef,
    IntArrayType,
    IntType,
    JeffModule,
    JeffOp,
    JeffRegion,
    JeffValue,
    PPRGate,
    QubitType,
    QuregType,
    WellKnowGate,
    load_module,
    pauli_rotation,
    quantum_gate,
    switch_case,
)


def test_func_call_reads_back() -> None:
    call = JeffOp("func", "funcCall", [], [], 1)
    main = FunctionDef(
        name="main", body=JeffRegion(sources=[], targets=[], operations=[call])
    )
    callee = FunctionDef(
        name="callee", body=JeffRegion(sources=[], targets=[], operations=[])
    )
    module = JeffModule([main, callee])
    module.refresh()

    loaded = JeffModule.from_encoding(module._raw_data)
    op = loaded.functions[0].body.operations[0]
    assert op.kind == "func"
    assert op.subkind == "funcCall"
    assert op.instruction_data == 1


def test_types_read_back() -> None:
    expected = [
        QubitType(),
        QuregType(),
        QuregType(3),
        IntType(8),
        IntArrayType(8),
        IntArrayType(8, 3),
        FloatType(32),
        FloatType(64),
        FloatArrayType(64),
        FloatArrayType(64, 3),
    ]
    values = [JeffValue(type) for type in expected]
    body = JeffRegion(sources=values, targets=values, operations=[])
    module = JeffModule([FunctionDef(name="main", body=body)])
    module.refresh()

    loaded = JeffModule.from_encoding(module._raw_data)
    assert loaded.functions[0].function_type == (expected, expected)


def test_gates_read_back() -> None:
    qubit = JeffValue(QubitType())
    control = JeffValue(QubitType())
    angle = JeffValue(FloatType(64))
    well_known = quantum_gate(
        "h", qubit, control_qubits=[control], adjoint=True, power=2
    )
    custom = quantum_gate("external", well_known.outputs)
    rotation = pauli_rotation(angle, ["x", "z"], custom.outputs)
    body = JeffRegion(
        sources=[qubit, control, angle],
        targets=rotation.outputs,
        operations=[well_known, custom, rotation],
    )
    module = JeffModule([FunctionDef(name="main", body=body)])
    module.refresh()

    loaded = JeffModule.from_encoding(module._raw_data)
    ops = loaded.functions[0].body.operations
    gate = ops[0].instruction_data
    assert isinstance(gate, WellKnowGate)
    assert gate.kind == "h"
    assert gate.num_controls == 1
    assert gate.adjoint
    assert gate.power == 2
    gate = ops[1].instruction_data
    assert isinstance(gate, CustomGate)
    assert gate.name == "external"
    assert gate.num_qubits == 2
    assert gate.num_params == 0
    gate = ops[2].instruction_data
    assert isinstance(gate, PPRGate)
    assert gate.pauli_string == ["x", "z"]
    assert ops[2].inputs[-1].type == FloatType(64)


def test_function_decl_reads_back(tmp_path: Path) -> None:
    qubit = JeffValue(QubitType())
    result = JeffValue(QubitType())
    call = JeffOp("func", "funcCall", [qubit], [result], 1)
    main = FunctionDef(
        name="main",
        body=JeffRegion(sources=[qubit], targets=[result], operations=[call]),
    )
    external = FunctionDecl(
        name="external", inputs=[QubitType()], outputs=[QubitType()]
    )
    module = JeffModule([main, external])
    path = tmp_path / "module.jeff"
    module.write_out(str(path))

    loaded = load_module(path)
    func = loaded.functions[1]
    assert isinstance(func, FunctionDecl)
    assert func.name == "external"
    assert func.function_type == ([QubitType()], [QubitType()])


def test_switch_without_default_reads_back() -> None:
    index = JeffValue(IntType(8))
    switch = switch_case(index, [], [JeffRegion(sources=[], targets=[], operations=[])])
    body = JeffRegion(sources=[index], targets=[], operations=[switch])
    module = JeffModule([FunctionDef(name="main", body=body)])
    module.refresh()

    loaded = JeffModule.from_encoding(module._raw_data)
    scf = loaded.functions[0].body.operations[0].instruction_data
    assert len(scf.branches) == 1
    assert scf.default is None
