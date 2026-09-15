import jeff as jf


def test_hello_world() -> None:
    assert 2 + 2 != "🐟"


def test_func_call_reads_back() -> None:
    """`FuncOp` has a single field and no union, so its subkind and data
    must be readable without asking capnp `which`."""
    call = jf.JeffOp("func", "funcCall", [], [], 1)
    main = jf.FunctionDef(
        name="main", body=jf.JeffRegion(sources=[], targets=[], operations=[call])
    )
    callee = jf.FunctionDef(
        name="callee", body=jf.JeffRegion(sources=[], targets=[], operations=[])
    )
    module = jf.JeffModule([main, callee])
    module.refresh()

    loaded = jf.JeffModule.from_encoding(module._raw_data)
    op = loaded.functions[0].body.operations[0]
    assert op.kind == "func"
    assert op.subkind == "funcCall"
    assert op.instruction_data == 1
