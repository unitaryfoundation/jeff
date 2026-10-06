from pathlib import Path

from jeff import FunctionDef, JeffModule, JeffOp, JeffRegion, load_module


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


def _module() -> JeffModule:
    call = JeffOp("func", "funcCall", [], [], 1)
    main = FunctionDef(
        name="main", body=JeffRegion(sources=[], targets=[], operations=[call])
    )
    callee = FunctionDef(
        name="callee", body=JeffRegion(sources=[], targets=[], operations=[])
    )
    return JeffModule([main, callee], tool="test")


def test_to_bytes_matches_the_written_file(tmp_path: Path) -> None:
    module = _module()
    path = tmp_path / "module.jeff"
    module.write_out(str(path))

    assert module.to_bytes() == path.read_bytes()


def test_from_bytes_reads_back() -> None:
    data = _module().to_bytes()

    loaded = JeffModule.from_bytes(data)
    del data
    assert [func.name for func in loaded.functions] == ["main", "callee"]
    assert loaded.functions[0].body.operations[0].subkind == "funcCall"
    assert loaded.tool == "test"


def test_from_bytes_reads_a_written_file(tmp_path: Path) -> None:
    path = tmp_path / "module.jeff"
    _module().write_out(str(path))

    from_bytes = JeffModule.from_bytes(path.read_bytes())
    assert from_bytes.to_bytes() == load_module(path).to_bytes()
