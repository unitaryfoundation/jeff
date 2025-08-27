"""
This API wraps the pycapnp bindings for the jeff exchange format.

The classes can be used both for zero-copy reading of an encoded program, as well as
for building and encoding new programs. It is *not* meant for extensive manipulations
of existing programs.

Reading a module can be done with the `load_module` function, while building is done by
instantiating the relevant classes. However many instructions like gates come with convenience
builder functions to instantiate the relevant classes.

When building a new program, never assign objects from an existing program, always use new objects!
Disregarding this advice could lead to unexpected behaviour.

All classes come with pretty-print string representation. Note that parsing is a non-goal.

.. data:: JEFF_VERSION

    Current version of the *jeff* format.

"""

from __future__ import annotations
from typing import Annotated, Type

from jeff.op.qubit.non_unitary import QubitAlloc, QubitFree
from jeff.op.scf import SwitchSCF
from jeff.region import Region

from .module import Module
from .op import JeffOp
from .op.qubit import PPRGate, QubitGate, Pauli
from .type import FloatType, IntType, JeffType, QubitType
from .value import Value

from .capnp import schema


# This is updated by our release-please workflow, triggered by this
# annotation: x-release-please-version
__version__ = "0.1.0"

# Current version of the *jeff* format.
JEFF_VERSION = Annotated[str, "feet"]

# TODO: add remaining op instructions
# TODO: add metadata support

################
# Reading      #
################


def load_module(path: str) -> Module:
    """Load a jeff module from file."""

    with open(path, "rb") as f:
        return Module._read_from_buffer(schema.Module.read(f))  # type: ignore


#################
# Building      #
#################


def qubit_alloc() -> JeffOp:
    """Single qubit alloc operation."""
    inputs: list[Value] = []
    outputs = [Value(QubitType())]
    return JeffOp(QubitAlloc(), inputs, outputs)


def qubit_free(qubit: Value) -> JeffOp:
    """Single qubit free operation."""
    inputs = [qubit]
    outputs: list[Value] = []
    return JeffOp(QubitFree(), inputs, outputs)


def quantum_gate(
    name: str,
    qubits: Value | list[Value],
    params: list[Value] | None = None,
    *,
    control_qubits: list[Value] | None = None,
    adjoint: bool = False,
    power: int = 1,
) -> JeffOp:
    """Instantiate a well-known or custom gate operation."""
    qubits = [qubits] if isinstance(qubits, Value) else qubits
    params = params or []
    control_qubits = control_qubits or []

    _check_values(qubits, QubitType, "Qubit")
    _check_values(control_qubits, QubitType, "Control qubit")
    _check_values(params, FloatType, "Parameter")

    gate = QubitGate.from_gate_name(
        name,
        num_qubits=len(qubits),
        num_params=len(params),
        num_controls=len(control_qubits),
        adjoint=adjoint,
        power=power,
    )
    qubit_inputs = qubits + control_qubits
    inputs = qubit_inputs + params
    outputs = [Value(QubitType()) for _ in qubit_inputs]
    return JeffOp(gate, inputs, outputs)


def pauli_rotation(
    angle: Value,
    pauli_string: Pauli | str | list[Pauli | str],
    qubits: Value | list[Value],
    *,
    control_qubits: list[Value] | None = None,
    adjoint: bool = False,
    power: int = 1,
) -> JeffOp:
    """Instantiate a Pauli-product rotation operation."""

    if not isinstance(pauli_string, list):
        pauli_string = [pauli_string]

    for i, pauli in enumerate(pauli_string):
        if isinstance(pauli, str):
            pauli_string[i] = Pauli.from_name(pauli)

    qubits = [qubits] if isinstance(qubits, Value) else qubits
    control_qubits = control_qubits or []

    assert len(pauli_string) == len(qubits), (
        f"Pauli string length {len(pauli_string)} must match number of qubits {len(qubits)}"
    )
    _check_values(qubits, QubitType, "Qubit")
    _check_values(control_qubits, QubitType, "Control qubit")
    _check_values(angle, FloatType, "Pauli angle")

    ppr = PPRGate(
        pauli_string, num_controls=len(control_qubits), adjoint=adjoint, power=power
    )
    inputs = qubits + control_qubits + [angle]
    outputs = [Value(QubitType()) for _ in inputs[:-1]]
    return JeffOp(ppr, inputs, outputs)


# TODO: Unimplemented
# def bitwise_not(x: Value):
#    """Instantiate a bitwise NOT operation."""
#    inputs = [x]
#    outputs = [Value(x.type)]
#    #return JeffOp("", inputs, outputs)


def switch_case(
    index: Value,
    region_args: list[Value],
    branches: list[Region],
    default: Region | None = None,
) -> JeffOp:
    """Instantiate a switch-case operation. Cases run from 0 to len(branches)-1.

    If the value of the index is out of bounds, the default branch is executed.

    :param index: The index value to switch on.
    :param region_args: The arguments to pass to the regions.
    :param branches: The branches to switch to.
    :param default: The default branch to switch to if the index is out of bounds.
    """
    _check_values(index, IntType, "Index")

    for branch in branches + [default] if default else branches:
        assert len(branch.sources) == len(branches[0].sources), (
            "all branches require the same number of sources"
        )
        assert all(
            map(lambda x, y: x.type == y.type, branch.sources, branches[0].sources)
        ), "all branches require the same source type signature"
        assert len(branch.targets) == len(branches[0].targets), (
            "all branches require the same number of targets"
        )
        assert all(
            map(lambda x, y: x.type == y.type, branch.targets, branches[0].targets)
        ), "all branches require the same target type signature"
    assert all(map(lambda x, y: x.type == y.type, region_args, branches[0].sources)), (
        "the initial region_args must match the source type signature of the branches"
    )

    scf = SwitchSCF(branches, default)
    inputs = [index] + region_args
    outputs = [Value(val.type) for val in branches[0].targets]

    return JeffOp(scf, inputs, outputs)


def _check_values(
    values: Value | list[Value], expected_type: Type[JeffType], name: str
) -> None:
    """Check that the values have valid types."""
    values = [values] if isinstance(values, Value) else values
    for value in values:
        if not isinstance(value.type, expected_type):
            raise ValueError(f"{name} {value} must be a {expected_type}")
