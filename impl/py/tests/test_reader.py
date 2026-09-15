from jeff import FunctionDef, JeffModule, JeffOp, JeffRegion


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
