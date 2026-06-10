"""Generate .jeff (and companion .txt) test case files for the verifier.

Run from the repo root:
    .venv/bin/python tools/verifier/tests/generate_test_cases.py

Each call to _write() produces both a binary .jeff file and a human-readable .txt
file (via `capnp decode`) in the same directory.

Tests implemented via hand-crafted .txt sources (not generated here):
  - entrypoint_is_declaration  : Python lib crashes on FunctionDecl.body in _compute_strings
  - OOB value-reference tests  : Python lib assigns IDs automatically; can't produce OOB refs
  - Qureg op type tests        : Python lib has no qureg op support
  - Alloc unexpected input     : same — requires manual capnp text
  - Free / Reset with output   : same
  - Gate wrong arity tests     : same
  Source .txt files live in tests/negative/encode/.
  Run tests/encode_test_cases.sh to produce their .jeff files.

Deferred (not implemented, caught by the reader not the verifier):
  - test_unsupported_schema_version : rejected by Jeff::read before verify_module is called
"""

import subprocess
from pathlib import Path

import semver

from jeff import (
    CustomGate,
    DoWhileSCF,
    FunctionDef,
    ForSCF,
    JeffModule,
    JeffOp,
    JeffRegion,
    JeffValue,
    IntType,
    FloatType,
    QubitType,
    SwitchSCF,
    WhileSCF,
    qubit_alloc,
    qubit_free,
    quantum_gate,
)

POSITIVE_DIR = Path(__file__).parent / "positive"
NEG_MODULE = Path(__file__).parent / "negative" / "module"
NEG_ORDERING = Path(__file__).parent / "negative" / "ordering"
NEG_TYPES = Path(__file__).parent / "negative" / "types"
NEG_LINEARITY = Path(__file__).parent / "negative" / "linearity"
NEG_SCOPING = Path(__file__).parent / "negative" / "scoping"

_SCHEMA = Path(__file__).parents[3] / "impl" / "capnp" / "jeff.capnp"

VERSION = semver.Version(0, 2, 0)
VERSION_ZERO = semver.Version(0, 0, 0)


def _write(module: JeffModule, directory: Path, name: str) -> None:
    jeff_path = directory / name
    module.write_out(jeff_path)
    txt_path = jeff_path.with_suffix(".txt")
    with open(jeff_path, "rb") as f_in, open(txt_path, "w") as f_out:
        subprocess.run(
            ["capnp", "decode", str(_SCHEMA), "Module"],
            stdin=f_in,
            stdout=f_out,
            check=True,
        )


# ──────────────────────────────────────────────
# Positive tests
# ──────────────────────────────────────────────


def generate_valid_comprehensive() -> None:
    """One file that exercises every feature the verifier checks."""

    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c20 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 20)
    iadd = JeffOp(
        "int", "add", [c10.outputs[0], c20.outputs[0]], [JeffValue(IntType(32))]
    )
    ieq = JeffOp("int", "eq", [c10.outputs[0], c20.outputs[0]], [JeffValue(IntType(1))])

    f1 = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 1.0)
    f2 = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 2.0)
    fadd = JeffOp(
        "float", "add", [f1.outputs[0], f2.outputs[0]], [JeffValue(FloatType(64))]
    )
    flt = JeffOp("float", "lt", [f1.outputs[0], f2.outputs[0]], [JeffValue(IntType(1))])

    alloc_h = qubit_alloc()
    gate_h = quantum_gate("H", alloc_h.outputs[0])
    measure = JeffOp("qubit", "measure", [gate_h.outputs[0]], [JeffValue(IntType(1))])

    alloc_rx = qubit_alloc()
    gate_rx = quantum_gate("Rx", alloc_rx.outputs[0], params=[f1.outputs[0]])
    measure_nd = JeffOp(
        "qubit",
        "measureNd",
        [gate_rx.outputs[0]],
        [JeffValue(QubitType()), JeffValue(IntType(1))],
    )
    free_q = qubit_free(measure_nd.outputs[0])

    for_iter = JeffValue(IntType(32))
    for_state_in = JeffValue(IntType(32))
    for_c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    for_add = JeffOp(
        "int", "add", [for_state_in, for_c1.outputs[0]], [JeffValue(IntType(32))]
    )
    for_body = JeffRegion(
        sources=[for_iter, for_state_in],
        targets=[for_add.outputs[0]],
        operations=[for_c1, for_add],
    )
    for_op = JeffOp(
        "scf",
        "for",
        [c10.outputs[0], iadd.outputs[0], c10.outputs[0], c20.outputs[0]],
        [JeffValue(IntType(32))],
        ForSCF(for_body),
    )

    w_cond_src = JeffValue(IntType(1))
    w_cond_not = JeffOp("int", "not", [w_cond_src], [JeffValue(IntType(1))])
    while_cond = JeffRegion(
        sources=[w_cond_src], targets=[w_cond_not.outputs[0]], operations=[w_cond_not]
    )
    w_body_src = JeffValue(IntType(1))
    w_body_not = JeffOp("int", "not", [w_body_src], [JeffValue(IntType(1))])
    while_body = JeffRegion(
        sources=[w_body_src], targets=[w_body_not.outputs[0]], operations=[w_body_not]
    )
    while_op = JeffOp(
        "scf",
        "while",
        [ieq.outputs[0]],
        [JeffValue(IntType(1))],
        WhileSCF(while_cond, while_body),
    )

    dw_body_src = JeffValue(IntType(32))
    dw_body_c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    dw_body_add = JeffOp(
        "int", "add", [dw_body_src, dw_body_c1.outputs[0]], [JeffValue(IntType(32))]
    )
    dowhile_body = JeffRegion(
        sources=[dw_body_src],
        targets=[dw_body_add.outputs[0]],
        operations=[dw_body_c1, dw_body_add],
    )
    dw_cond_src = JeffValue(IntType(32))
    dw_cond_c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    dw_cond_eq = JeffOp(
        "int", "eq", [dw_cond_src, dw_cond_c10.outputs[0]], [JeffValue(IntType(1))]
    )
    dowhile_cond = JeffRegion(
        sources=[dw_cond_src],
        targets=[dw_cond_eq.outputs[0]],
        operations=[dw_cond_c10, dw_cond_eq],
    )
    dowhile_op = JeffOp(
        "scf",
        "doWhile",
        [iadd.outputs[0]],
        [JeffValue(IntType(32))],
        DoWhileSCF(dowhile_body, dowhile_cond),
    )

    sw_b0_src = JeffValue(IntType(32))
    sw_b0_c99 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 99)
    sw_b0_add = JeffOp(
        "int", "add", [sw_b0_src, sw_b0_c99.outputs[0]], [JeffValue(IntType(32))]
    )
    sw_branch0 = JeffRegion(
        sources=[sw_b0_src],
        targets=[sw_b0_add.outputs[0]],
        operations=[sw_b0_c99, sw_b0_add],
    )
    sw_def_src = JeffValue(IntType(32))
    sw_default = JeffRegion(sources=[sw_def_src], targets=[sw_def_src], operations=[])
    switch_op = JeffOp(
        "scf",
        "switch",
        [flt.outputs[0], iadd.outputs[0]],
        [JeffValue(IntType(32))],
        SwitchSCF([sw_branch0], sw_default),
    )

    body = JeffRegion(
        sources=[],
        targets=[],
        operations=[
            c10,
            c20,
            iadd,
            ieq,
            f1,
            f2,
            fadd,
            flt,
            alloc_h,
            gate_h,
            measure,
            alloc_rx,
            gate_rx,
            measure_nd,
            free_q,
            for_op,
            while_op,
            dowhile_op,
            switch_op,
        ],
    )
    _write(
        JeffModule(
            [FunctionDef(name="main", body=body)], version=VERSION, entrypoint=0
        ),
        POSITIVE_DIR,
        "valid_comprehensive.jeff",
    )


def generate_valid_minimal() -> None:
    """Empty-body function — the smallest valid program."""
    body = JeffRegion(sources=[], targets=[], operations=[])
    _write(
        JeffModule(
            [FunctionDef(name="minimal", body=body)], version=VERSION, entrypoint=0
        ),
        POSITIVE_DIR,
        "valid_minimal.jeff",
    )


def generate_valid_deeply_nested() -> None:
    """For loop nested inside another for loop, both properly isolated."""
    c0 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)

    inner_iter = JeffValue(IntType(32))
    inner_state = JeffValue(IntType(32))
    inner_c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    inner_add = JeffOp(
        "int", "add", [inner_state, inner_c1.outputs[0]], [JeffValue(IntType(32))]
    )
    inner_body = JeffRegion(
        sources=[inner_iter, inner_state],
        targets=[inner_add.outputs[0]],
        operations=[inner_c1, inner_add],
    )

    outer_iter = JeffValue(IntType(32))
    outer_state = JeffValue(IntType(32))
    oc0 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)
    oc10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    oc1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    inner_for = JeffOp(
        "scf",
        "for",
        [oc0.outputs[0], oc10.outputs[0], oc1.outputs[0], outer_state],
        [JeffValue(IntType(32))],
        ForSCF(inner_body),
    )
    outer_body = JeffRegion(
        sources=[outer_iter, outer_state],
        targets=[inner_for.outputs[0]],
        operations=[oc0, oc10, oc1, inner_for],
    )

    outer_for = JeffOp(
        "scf",
        "for",
        [c0.outputs[0], c10.outputs[0], c1.outputs[0], c0.outputs[0]],
        [JeffValue(IntType(32))],
        ForSCF(outer_body),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c0, c10, c1, outer_for])
    _write(
        JeffModule(
            [FunctionDef(name="main", body=body)], version=VERSION, entrypoint=0
        ),
        POSITIVE_DIR,
        "valid_deeply_nested.jeff",
    )


# ──────────────────────────────────────────────
# Negative: module attribute failures
# ──────────────────────────────────────────────


def _trivial_def() -> FunctionDef:
    return FunctionDef(name="f", body=JeffRegion(sources=[], targets=[], operations=[]))


def generate_missing_version() -> None:
    """Version 0.0.0 → MissingVersion."""
    _write(
        JeffModule([_trivial_def()], version=VERSION_ZERO, entrypoint=0),
        NEG_MODULE,
        "missing_version.jeff",
    )


def generate_entrypoint_oob() -> None:
    """Entrypoint index beyond function list → InvalidEntrypoint."""
    _write(
        JeffModule([_trivial_def()], version=VERSION, entrypoint=99),
        NEG_MODULE,
        "entrypoint_oob.jeff",
    )


def generate_no_functions() -> None:
    """Empty function list, version 0.0.0 → MissingVersion + InvalidEntrypoint."""
    _write(
        JeffModule([], version=VERSION_ZERO, entrypoint=0),
        NEG_MODULE,
        "no_functions.jeff",
    )


# ──────────────────────────────────────────────
# Negative: used before defined
# ──────────────────────────────────────────────


def generate_use_before_define_outer() -> None:
    """add uses c10 and c20 before they are defined in the outer region."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c20 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 20)
    add = JeffOp(
        "int", "add", [c10.outputs[0], c20.outputs[0]], [JeffValue(IntType(32))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[add, c10, c20])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_outer.jeff",
    )


def generate_use_before_define_for() -> None:
    """Inside for body: add uses a constant before the constant op appears."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c20 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 20)

    for_iter = JeffValue(IntType(32))
    for_state = JeffValue(IntType(32))
    late_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    bad_add = JeffOp(
        "int", "add", [for_state, late_c.outputs[0]], [JeffValue(IntType(32))]
    )
    for_body = JeffRegion(
        sources=[for_iter, for_state],
        targets=[bad_add.outputs[0]],
        operations=[bad_add, late_c],
    )  # bad_add before late_c

    for_op = JeffOp(
        "scf",
        "for",
        [c10.outputs[0], c20.outputs[0], c10.outputs[0], c10.outputs[0]],
        [JeffValue(IntType(32))],
        ForSCF(for_body),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c10, c20, for_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_for.jeff",
    )


def generate_use_before_define_while_cond() -> None:
    """Inside while condition: not uses a constant before the constant op appears."""
    c0 = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)

    cond_src = JeffValue(IntType(1))
    late_c = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)
    bad_not = JeffOp("int", "not", [late_c.outputs[0]], [JeffValue(IntType(1))])
    cond_reg = JeffRegion(
        sources=[cond_src], targets=[bad_not.outputs[0]], operations=[bad_not, late_c]
    )  # bad_not before late_c

    body_src = JeffValue(IntType(1))
    body_not = JeffOp("int", "not", [body_src], [JeffValue(IntType(1))])
    body_reg = JeffRegion(
        sources=[body_src], targets=[body_not.outputs[0]], operations=[body_not]
    )

    while_op = JeffOp(
        "scf",
        "while",
        [c0.outputs[0]],
        [JeffValue(IntType(1))],
        WhileSCF(cond_reg, body_reg),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c0, while_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_while_cond.jeff",
    )


def generate_use_before_define_while_body() -> None:
    """Inside while body: second not uses first not's output before first not appears."""
    c0 = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)

    cond_src = JeffValue(IntType(1))
    cond_not = JeffOp("int", "not", [cond_src], [JeffValue(IntType(1))])
    cond_reg = JeffRegion(
        sources=[cond_src], targets=[cond_not.outputs[0]], operations=[cond_not]
    )

    body_src = JeffValue(IntType(1))
    late_not = JeffOp("int", "not", [body_src], [JeffValue(IntType(1))])
    bad_not2 = JeffOp("int", "not", [late_not.outputs[0]], [JeffValue(IntType(1))])
    body_reg = JeffRegion(
        sources=[body_src],
        targets=[bad_not2.outputs[0]],
        operations=[bad_not2, late_not],
    )  # bad_not2 before late_not

    while_op = JeffOp(
        "scf",
        "while",
        [c0.outputs[0]],
        [JeffValue(IntType(1))],
        WhileSCF(cond_reg, body_reg),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c0, while_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_while_body.jeff",
    )


def generate_use_before_define_dowhile_body() -> None:
    """Inside dowhile body: add uses a constant before it appears."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)

    dw_src = JeffValue(IntType(32))
    late_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    bad_add = JeffOp(
        "int", "add", [dw_src, late_c.outputs[0]], [JeffValue(IntType(32))]
    )
    dw_body = JeffRegion(
        sources=[dw_src], targets=[bad_add.outputs[0]], operations=[bad_add, late_c]
    )  # bad_add before late_c

    cond_src = JeffValue(IntType(32))
    cond_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 5)
    cond_eq = JeffOp(
        "int", "eq", [cond_src, cond_c.outputs[0]], [JeffValue(IntType(1))]
    )
    dw_cond = JeffRegion(
        sources=[cond_src], targets=[cond_eq.outputs[0]], operations=[cond_c, cond_eq]
    )

    dw_op = JeffOp(
        "scf",
        "doWhile",
        [c10.outputs[0]],
        [JeffValue(IntType(32))],
        DoWhileSCF(dw_body, dw_cond),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c10, dw_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_dowhile_body.jeff",
    )


def generate_use_before_define_dowhile_cond() -> None:
    """Inside dowhile condition: eq uses a constant before it appears."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)

    dw_src = JeffValue(IntType(32))
    dw_c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    dw_add = JeffOp("int", "add", [dw_src, dw_c1.outputs[0]], [JeffValue(IntType(32))])
    dw_body = JeffRegion(
        sources=[dw_src], targets=[dw_add.outputs[0]], operations=[dw_c1, dw_add]
    )

    cond_src = JeffValue(IntType(32))
    late_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 5)
    bad_eq = JeffOp("int", "eq", [cond_src, late_c.outputs[0]], [JeffValue(IntType(1))])
    dw_cond = JeffRegion(
        sources=[cond_src], targets=[bad_eq.outputs[0]], operations=[bad_eq, late_c]
    )  # bad_eq before late_c

    dw_op = JeffOp(
        "scf",
        "doWhile",
        [c10.outputs[0]],
        [JeffValue(IntType(32))],
        DoWhileSCF(dw_body, dw_cond),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c10, dw_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_dowhile_cond.jeff",
    )


def generate_use_before_define_switch() -> None:
    """Inside a switch branch: add uses a constant before it appears."""
    c0 = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)

    b0_src = JeffValue(IntType(32))
    late_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 99)
    bad_add = JeffOp(
        "int", "add", [b0_src, late_c.outputs[0]], [JeffValue(IntType(32))]
    )
    branch0 = JeffRegion(
        sources=[b0_src], targets=[bad_add.outputs[0]], operations=[bad_add, late_c]
    )  # bad_add before late_c

    def_src = JeffValue(IntType(32))
    default = JeffRegion(sources=[def_src], targets=[def_src], operations=[])

    sw_op = JeffOp(
        "scf",
        "switch",
        [c0.outputs[0], c10.outputs[0]],
        [JeffValue(IntType(32))],
        SwitchSCF([branch0], default),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c0, c10, sw_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_ORDERING,
        "use_before_define_switch.jeff",
    )


# ──────────────────────────────────────────────
# Negative: type check failures
# ──────────────────────────────────────────────


def generate_int_add_mixed_bitwidths() -> None:
    """add(Int32, Int64) → TypeMismatch."""
    c32 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    c64 = JeffOp("int", "const64", [], [JeffValue(IntType(64))], 2)
    bad = JeffOp(
        "int", "add", [c32.outputs[0], c64.outputs[0]], [JeffValue(IntType(32))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[c32, c64, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "int_add_mixed_bitwidths.jeff",
    )


def generate_int_compare_mixed_bitwidths() -> None:
    """eq(Int32, Int64) → TypeMismatch for int comparison."""
    c32 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    c64 = JeffOp("int", "const64", [], [JeffValue(IntType(64))], 2)
    bad = JeffOp("int", "eq", [c32.outputs[0], c64.outputs[0]], [JeffValue(IntType(1))])
    body = JeffRegion(sources=[], targets=[], operations=[c32, c64, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "int_compare_mixed_bitwidths.jeff",
    )


def generate_int_compare_bad_output() -> None:
    """eq produces Int32 instead of Int1 → InvalidOutputType."""
    c32a = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    c32b = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 2)
    bad = JeffOp(
        "int", "eq", [c32a.outputs[0], c32b.outputs[0]], [JeffValue(IntType(32))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[c32a, c32b, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "int_compare_bad_output.jeff",
    )


def generate_int_unary_bad_output() -> None:
    """not(Int32) → Int64: mismatched bitwidth → TypeMismatch."""
    c32 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 5)
    bad = JeffOp("int", "not", [c32.outputs[0]], [JeffValue(IntType(64))])
    body = JeffRegion(sources=[], targets=[], operations=[c32, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "int_unary_bad_output.jeff",
    )


def generate_float_add_mixed_precisions() -> None:
    """add(Float32, Float64) → TypeMismatch."""
    f32 = JeffOp("float", "const32", [], [JeffValue(FloatType(32))], 1.0)
    f64 = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 2.0)
    bad = JeffOp(
        "float", "add", [f32.outputs[0], f64.outputs[0]], [JeffValue(FloatType(64))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[f32, f64, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "float_add_mixed_precisions.jeff",
    )


def generate_float_compare_mixed_precisions() -> None:
    """lt(Float32, Float64) → TypeMismatch for float predicate."""
    f32 = JeffOp("float", "const32", [], [JeffValue(FloatType(32))], 1.0)
    f64 = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 2.0)
    bad = JeffOp(
        "float", "lt", [f32.outputs[0], f64.outputs[0]], [JeffValue(IntType(1))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[f32, f64, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "float_compare_mixed_precisions.jeff",
    )


def generate_float_compare_bad_output() -> None:
    """lt produces Float64 instead of Int1 → InvalidOutputType."""
    f64a = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 1.0)
    f64b = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 2.0)
    bad = JeffOp(
        "float", "lt", [f64a.outputs[0], f64b.outputs[0]], [JeffValue(FloatType(64))]
    )
    body = JeffRegion(sources=[], targets=[], operations=[f64a, f64b, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "float_compare_bad_output.jeff",
    )


def generate_alloc_bad_output() -> None:
    """alloc produces Int32 instead of Qubit → InvalidOutputType."""
    bad = JeffOp("qubit", "alloc", [], [JeffValue(IntType(32))])
    body = JeffRegion(sources=[], targets=[], operations=[bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "alloc_bad_output.jeff",
    )


def generate_measure_bad_input() -> None:
    """measure takes Int32 instead of Qubit → InvalidInputType."""
    c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)
    bad = JeffOp("qubit", "measure", [c.outputs[0]], [JeffValue(IntType(1))])
    body = JeffRegion(sources=[], targets=[], operations=[c, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "measure_bad_input.jeff",
    )


def generate_measure_bad_output() -> None:
    """measure produces Float64 instead of Int1 → InvalidOutputType."""
    alloc = qubit_alloc()
    bad = JeffOp("qubit", "measure", [alloc.outputs[0]], [JeffValue(FloatType(64))])
    body = JeffRegion(sources=[], targets=[], operations=[alloc, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "measure_bad_output.jeff",
    )


def generate_measurend_bad_first_output() -> None:
    """measureNd first output is Int32 instead of Qubit → InvalidOutputType."""
    alloc = qubit_alloc()
    bad = JeffOp(
        "qubit",
        "measureNd",
        [alloc.outputs[0]],
        [JeffValue(IntType(32)), JeffValue(IntType(1))],
    )
    body = JeffRegion(sources=[], targets=[], operations=[alloc, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "measurend_bad_first_output.jeff",
    )


def generate_measurend_bad_second_output() -> None:
    """measureNd second output is Float64 instead of Int1 → InvalidOutputType."""
    alloc = qubit_alloc()
    bad = JeffOp(
        "qubit",
        "measureNd",
        [alloc.outputs[0]],
        [JeffValue(QubitType()), JeffValue(FloatType(64))],
    )
    free = qubit_free(bad.outputs[0])
    body = JeffRegion(sources=[], targets=[], operations=[alloc, bad, free])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "measurend_bad_second_output.jeff",
    )


def generate_free_bad_input() -> None:
    """free takes Float64 instead of Qubit → InvalidInputType."""
    f = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 0.0)
    bad = JeffOp("qubit", "free", [f.outputs[0]], [])
    body = JeffRegion(sources=[], targets=[], operations=[f, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "free_bad_input.jeff",
    )


def generate_gate_bad_qubit_input() -> None:
    """gate first input is Float64 instead of Qubit → InvalidInputType."""
    f = JeffOp("float", "const64", [], [JeffValue(FloatType(64))], 1.0)
    bad = JeffOp(
        "qubit",
        "gate",
        [f.outputs[0]],
        [JeffValue(QubitType())],
        CustomGate("bad", 1, 0, 0, False, 1),
    )
    body = JeffRegion(sources=[], targets=[], operations=[f, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "gate_bad_qubit_input.jeff",
    )


def generate_gate_bad_qubit_output() -> None:
    """gate output is Float64 instead of Qubit → InvalidOutputType."""
    alloc = qubit_alloc()
    bad = JeffOp(
        "qubit",
        "gate",
        [alloc.outputs[0]],
        [JeffValue(FloatType(64))],
        CustomGate("bad", 1, 0, 0, False, 1),
    )
    body = JeffRegion(sources=[], targets=[], operations=[alloc, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "gate_bad_qubit_output.jeff",
    )


def generate_gate_bad_param_type() -> None:
    """gate float parameter is Int32 instead of Float → InvalidInputType."""
    alloc = qubit_alloc()
    c_int = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    bad = JeffOp(
        "qubit",
        "gate",
        [alloc.outputs[0], c_int.outputs[0]],
        [JeffValue(QubitType())],
        CustomGate("bad", 1, 1, 0, False, 1),
    )
    body = JeffRegion(sources=[], targets=[], operations=[alloc, c_int, bad])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_TYPES,
        "gate_bad_param_type.jeff",
    )


# ──────────────────────────────────────────────
# Negative: linearity violations
# ──────────────────────────────────────────────


def generate_qubit_produced_twice() -> None:
    """Same qubit value appears as both body source and op output → LinearValueProducedMultipleTimes."""
    q = JeffValue(QubitType())
    alloc = JeffOp("qubit", "alloc", [], [q])  # op produces q
    free = qubit_free(q)  # op consumes q
    body = JeffRegion(sources=[q], targets=[], operations=[alloc, free])
    # q: producers = 2 (source + alloc output), consumers = 1 (free)
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_LINEARITY,
        "qubit_produced_twice.jeff",
    )


def generate_qubit_consumed_twice() -> None:
    """Same qubit value used as input by two ops → LinearValueConsumedMultipleTimes."""
    alloc = qubit_alloc()
    meas1 = JeffOp("qubit", "measure", [alloc.outputs[0]], [JeffValue(IntType(1))])
    meas2 = JeffOp("qubit", "measure", [alloc.outputs[0]], [JeffValue(IntType(1))])
    body = JeffRegion(sources=[], targets=[], operations=[alloc, meas1, meas2])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_LINEARITY,
        "qubit_consumed_twice.jeff",
    )


def generate_qubit_never_consumed() -> None:
    """Qubit allocated but never freed or measured → LinearValueNeverConsumed."""
    alloc = qubit_alloc()
    body = JeffRegion(sources=[], targets=[], operations=[alloc])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_LINEARITY,
        "qubit_never_consumed.jeff",
    )


# ──────────────────────────────────────────────
# Negative: isolation / scoping violations
# ──────────────────────────────────────────────


def generate_for_captures_outer() -> None:
    """For body directly uses a value from the outer scope → IsolationViolation."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c20 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 20)

    for_iter = JeffValue(IntType(32))
    for_state = JeffValue(IntType(32))
    bad_add = JeffOp(
        "int", "add", [for_state, c10.outputs[0]], [JeffValue(IntType(32))]
    )
    # c10.outputs[0] is from the outer region — not a source of this body
    for_body = JeffRegion(
        sources=[for_iter, for_state],
        targets=[bad_add.outputs[0]],
        operations=[bad_add],
    )

    for_op = JeffOp(
        "scf",
        "for",
        [c10.outputs[0], c20.outputs[0], c10.outputs[0], c10.outputs[0]],
        [JeffValue(IntType(32))],
        ForSCF(for_body),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c10, c20, for_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "for_captures_outer.jeff",
    )


def generate_while_cond_captures_outer() -> None:
    """While condition directly uses an outer value → IsolationViolation."""
    c_outer = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)
    c_init = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)

    cond_src = JeffValue(IntType(1))
    # bad: uses c_outer.outputs[0] which is from the outer region
    bad_not = JeffOp("int", "not", [c_outer.outputs[0]], [JeffValue(IntType(1))])
    cond_reg = JeffRegion(
        sources=[cond_src], targets=[bad_not.outputs[0]], operations=[bad_not]
    )

    body_src = JeffValue(IntType(1))
    body_not = JeffOp("int", "not", [body_src], [JeffValue(IntType(1))])
    body_reg = JeffRegion(
        sources=[body_src], targets=[body_not.outputs[0]], operations=[body_not]
    )

    while_op = JeffOp(
        "scf",
        "while",
        [c_init.outputs[0]],
        [JeffValue(IntType(1))],
        WhileSCF(cond_reg, body_reg),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c_outer, c_init, while_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "while_cond_captures_outer.jeff",
    )


def generate_while_body_captures_outer() -> None:
    """While body directly uses an outer value → IsolationViolation."""
    c_outer = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)
    c_init = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)

    cond_src = JeffValue(IntType(1))
    cond_not = JeffOp("int", "not", [cond_src], [JeffValue(IntType(1))])
    cond_reg = JeffRegion(
        sources=[cond_src], targets=[cond_not.outputs[0]], operations=[cond_not]
    )

    body_src = JeffValue(IntType(1))
    # bad: uses c_outer.outputs[0] which is from the outer region
    bad_not = JeffOp("int", "not", [c_outer.outputs[0]], [JeffValue(IntType(1))])
    body_reg = JeffRegion(
        sources=[body_src], targets=[bad_not.outputs[0]], operations=[bad_not]
    )

    while_op = JeffOp(
        "scf",
        "while",
        [c_init.outputs[0]],
        [JeffValue(IntType(1))],
        WhileSCF(cond_reg, body_reg),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c_outer, c_init, while_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "while_body_captures_outer.jeff",
    )


def generate_dowhile_body_captures_outer() -> None:
    """DoWhile body directly uses an outer value → IsolationViolation."""
    c_outer = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 99)
    c_init = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)

    dw_src = JeffValue(IntType(32))
    # bad: uses c_outer.outputs[0] which is from the outer region
    bad_add = JeffOp(
        "int", "add", [dw_src, c_outer.outputs[0]], [JeffValue(IntType(32))]
    )
    dw_body = JeffRegion(
        sources=[dw_src], targets=[bad_add.outputs[0]], operations=[bad_add]
    )

    cond_src = JeffValue(IntType(32))
    cond_c = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 5)
    cond_eq = JeffOp(
        "int", "eq", [cond_src, cond_c.outputs[0]], [JeffValue(IntType(1))]
    )
    dw_cond = JeffRegion(
        sources=[cond_src], targets=[cond_eq.outputs[0]], operations=[cond_c, cond_eq]
    )

    dw_op = JeffOp(
        "scf",
        "doWhile",
        [c_init.outputs[0]],
        [JeffValue(IntType(32))],
        DoWhileSCF(dw_body, dw_cond),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c_outer, c_init, dw_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "dowhile_body_captures_outer.jeff",
    )


def generate_dowhile_cond_captures_outer() -> None:
    """DoWhile condition directly uses an outer value → IsolationViolation."""
    c_outer = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 5)
    c_init = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)

    dw_src = JeffValue(IntType(32))
    dw_c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    dw_add = JeffOp("int", "add", [dw_src, dw_c1.outputs[0]], [JeffValue(IntType(32))])
    dw_body = JeffRegion(
        sources=[dw_src], targets=[dw_add.outputs[0]], operations=[dw_c1, dw_add]
    )

    cond_src = JeffValue(IntType(32))
    # bad: uses c_outer.outputs[0] which is from the outer region
    bad_eq = JeffOp(
        "int", "eq", [cond_src, c_outer.outputs[0]], [JeffValue(IntType(1))]
    )
    dw_cond = JeffRegion(
        sources=[cond_src], targets=[bad_eq.outputs[0]], operations=[bad_eq]
    )

    dw_op = JeffOp(
        "scf",
        "doWhile",
        [c_init.outputs[0]],
        [JeffValue(IntType(32))],
        DoWhileSCF(dw_body, dw_cond),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c_outer, c_init, dw_op])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "dowhile_cond_captures_outer.jeff",
    )


def generate_switch_captures_outer() -> None:
    """Switch branch directly uses an outer value → IsolationViolation."""
    c_outer = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 99)
    c_idx = JeffOp("int", "const32", [], [JeffValue(IntType(1))], 0)
    c_state = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)

    b0_src = JeffValue(IntType(32))
    # bad: uses c_outer.outputs[0] which is from the outer region
    bad_add = JeffOp(
        "int", "add", [b0_src, c_outer.outputs[0]], [JeffValue(IntType(32))]
    )
    branch0 = JeffRegion(
        sources=[b0_src], targets=[bad_add.outputs[0]], operations=[bad_add]
    )

    def_src = JeffValue(IntType(32))
    default = JeffRegion(sources=[def_src], targets=[def_src], operations=[])

    sw_op = JeffOp(
        "scf",
        "switch",
        [c_idx.outputs[0], c_state.outputs[0]],
        [JeffValue(IntType(32))],
        SwitchSCF([branch0], default),
    )
    body = JeffRegion(
        sources=[], targets=[], operations=[c_outer, c_idx, c_state, sw_op]
    )
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "switch_captures_outer.jeff",
    )


def generate_nested_captures_grandparent() -> None:
    """Inner for body uses a value from the outer function scope (grandparent) → IsolationViolation."""
    c10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    c20 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 20)
    c1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)

    inner_iter = JeffValue(IntType(32))
    inner_state = JeffValue(IntType(32))
    # bad: c10.outputs[0] is from the grandparent scope (outer function body)
    bad_add = JeffOp(
        "int", "add", [inner_state, c10.outputs[0]], [JeffValue(IntType(32))]
    )
    inner_body = JeffRegion(
        sources=[inner_iter, inner_state],
        targets=[bad_add.outputs[0]],
        operations=[bad_add],
    )

    outer_iter = JeffValue(IntType(32))
    outer_state = JeffValue(IntType(32))
    oc0 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 0)
    oc10 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 10)
    oc1 = JeffOp("int", "const32", [], [JeffValue(IntType(32))], 1)
    inner_for = JeffOp(
        "scf",
        "for",
        [oc0.outputs[0], oc10.outputs[0], oc1.outputs[0], outer_state],
        [JeffValue(IntType(32))],
        ForSCF(inner_body),
    )
    outer_body = JeffRegion(
        sources=[outer_iter, outer_state],
        targets=[inner_for.outputs[0]],
        operations=[oc0, oc10, oc1, inner_for],
    )

    outer_for = JeffOp(
        "scf",
        "for",
        [c10.outputs[0], c20.outputs[0], c1.outputs[0], c10.outputs[0]],
        [JeffValue(IntType(32))],
        ForSCF(outer_body),
    )
    body = JeffRegion(sources=[], targets=[], operations=[c10, c20, c1, outer_for])
    _write(
        JeffModule([FunctionDef(name="f", body=body)], version=VERSION, entrypoint=0),
        NEG_SCOPING,
        "nested_captures_grandparent.jeff",
    )


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────


if __name__ == "__main__":
    POSITIVE_DIR.mkdir(exist_ok=True)
    for d in (NEG_MODULE, NEG_ORDERING, NEG_TYPES, NEG_LINEARITY, NEG_SCOPING):
        d.mkdir(parents=True, exist_ok=True)

    generate_valid_comprehensive()
    generate_valid_minimal()
    generate_valid_deeply_nested()

    generate_missing_version()
    generate_entrypoint_oob()
    generate_no_functions()

    generate_use_before_define_outer()
    generate_use_before_define_for()
    generate_use_before_define_while_cond()
    generate_use_before_define_while_body()
    generate_use_before_define_dowhile_body()
    generate_use_before_define_dowhile_cond()
    generate_use_before_define_switch()

    generate_int_add_mixed_bitwidths()
    generate_int_compare_mixed_bitwidths()
    generate_int_compare_bad_output()
    generate_int_unary_bad_output()
    generate_float_add_mixed_precisions()
    generate_float_compare_mixed_precisions()
    generate_float_compare_bad_output()
    generate_alloc_bad_output()
    generate_measure_bad_input()
    generate_measure_bad_output()
    generate_measurend_bad_first_output()
    generate_measurend_bad_second_output()
    generate_free_bad_input()
    generate_gate_bad_qubit_input()
    generate_gate_bad_qubit_output()
    generate_gate_bad_param_type()

    generate_qubit_produced_twice()
    generate_qubit_consumed_twice()
    generate_qubit_never_consumed()

    generate_for_captures_outer()
    generate_while_cond_captures_outer()
    generate_while_body_captures_outer()
    generate_dowhile_body_captures_outer()
    generate_dowhile_cond_captures_outer()
    generate_switch_captures_outer()
    generate_nested_captures_grandparent()

    print("done")
