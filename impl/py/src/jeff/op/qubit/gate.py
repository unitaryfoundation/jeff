"""Qubit gates and operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import override

from jeff.op.kind import OpKind

from jeff.capnp import LazyUpdate, schema
from jeff.op.qubit import QubitOp
from jeff.string_table import StringTable


class Pauli(Enum):
    I = "i"  # noqa: E741
    X = "x"
    Y = "y"
    Z = "z"

    @staticmethod
    def from_name(name: str) -> Pauli:
        """Try to match a Pauli name to a known Pauli."""
        match name.lower():
            case "i":
                return Pauli.I
            case "x":
                return Pauli.X
            case "y":
                return Pauli.Y
            case "z":
                return Pauli.Z
        raise ValueError(f"unknown Pauli: {name}")


class KnownGate(Enum):
    """A standard quantum gate.

    Well-known gates must be one of the gates defined in the spec. No additional
    data needs to be specified."""

    GPHASE = "gphase"
    I = "i"  # noqa: E741
    X = "x"
    Y = "y"
    Z = "z"
    S = "s"
    T = "t"
    RX = "rx"
    RY = "ry"
    RZ = "rz"
    H = "h"
    U = "u"
    SWAP = "swap"

    # convenience methods

    @property
    def num_qubits(self) -> int:
        match self:
            case KnownGate.GPHASE:
                return 0
            case (
                KnownGate.I
                | KnownGate.X
                | KnownGate.Y
                | KnownGate.Z
                | KnownGate.S
                | KnownGate.T
                | KnownGate.RX
                | KnownGate.RY
                | KnownGate.RZ
                | KnownGate.H
                | KnownGate.U
            ):
                return 1
            case KnownGate.SWAP:
                return 2
            case _:
                raise ValueError(f"unknown gate: {self.value}")

    @property
    def num_params(self) -> int:
        match self:
            case (
                KnownGate.I
                | KnownGate.X
                | KnownGate.Y
                | KnownGate.Z
                | KnownGate.S
                | KnownGate.T
                | KnownGate.H
                | KnownGate.SWAP
            ):
                return 0
            case KnownGate.GPHASE | KnownGate.RX | KnownGate.RY | KnownGate.RZ:
                return 1
            case KnownGate.U:
                return 3
            case _:
                raise ValueError(f"unknown gate: {self.value}")

    @staticmethod
    def from_name(name: str) -> KnownGate:
        """Try to match a quantum gate name to a known gate.

        :raises ValueError: If the name does not match any known gate.
        """
        name = name.lower()
        for gate in KnownGate:
            if name == gate.value:
                return gate
        raise ValueError(f"unknown gate: {name}")


class QubitGate(
    ABC,
    QubitOp[schema.QubitGate, schema.QubitGate.Builder],  # type: ignore
    LazyUpdate,
):
    """Instruction data for quantum gate operations."""

    _num_controls: int = 0
    _adjoint: bool = False
    _power: int = 1

    # The read-only buffer backing this object.
    _raw_data: schema.QubitGate | None = None  # type: ignore

    @staticmethod
    def from_gate_name(
        name: str,
        *,
        num_qubits: int,
        num_params: int,
        num_controls: int = 0,
        adjoint: bool = False,
        power: int = 1,
    ) -> QubitGate:
        """Return a qubit gate from a name, trying to match a well-known names if possible.

        :param name: The name of the gate.
        :param num_qubits: The number of qubits the gate acts on.
        :param num_params: The number of float parameters to the gate.
        :param num_controls: The number of control qubits.
        """
        try:
            gate = KnownGate.from_name(name)
            # Only use the well-known gate if it matches the number of qubits and parameters
            if gate.num_qubits == num_qubits and gate.num_params == num_params:
                return WellKnownGate(
                    gate, num_controls=num_controls, adjoint=adjoint, power=power
                )
        except ValueError:
            pass

        return CustomGate(
            name,
            num_qubits,
            num_params,
            num_controls=num_controls,
            adjoint=adjoint,
            power=power,
        )

    @override
    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._op:
            self._op._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: schema.QubitGate) -> QubitGate:  # type: ignore
        match reader.which:
            case "custom":
                gate = CustomGate._read_from_buffer(reader.custom)
            case "wellKnown":
                gate = WellKnownGate._read_from_buffer(reader.wellKnown)
            case "ppr":
                gate = PPRGate._read_from_buffer(reader.ppr)
            case _:
                raise ValueError(f"unknown gate type: {reader.which}")
        gate._num_controls = reader.controlQubits
        gate._adjoint = reader.adjoint
        gate._power = reader.power
        gate._mark_clean()
        return gate

    def _force_read_all(self) -> None:
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.QubitGate.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        writer.controlQubits = self.num_controls
        writer.adjoint = self.adjoint
        writer.power = self.power
        self._raw_data = writer.as_reader()
        self._mark_clean()

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        """Number of qubits the gate acts on, not including control qubits."""

    @property
    @abstractmethod
    def num_params(self) -> int:
        """Number of float parameters to the gate."""

    @property
    def op_kind(self) -> OpKind:
        """The kind of operation."""
        return OpKind.QUBIT_GATE

    @property
    @abstractmethod
    def qualified_name(self) -> str:
        """The name of the gate, including the 'qubit.gate.' prefix."""

    # settable fields

    @property
    def num_controls(self) -> int:
        """Number of control qubits."""
        return self._num_controls

    @num_controls.setter
    def num_controls(self, num_controls: int) -> None:
        """Set the number of control qubits."""
        self._num_controls = num_controls
        self._mark_dirty()

    @property
    def adjoint(self) -> bool:
        """Whether the gate is adjoint."""
        return self._adjoint

    @adjoint.setter
    def adjoint(self, adjoint: bool) -> None:
        """Set whether the gate is adjoint."""
        self._adjoint = adjoint
        self._mark_dirty()

    @property
    def power(self) -> int:
        """Times the gate is applied."""
        return self._power

    @power.setter
    def power(self, power: int) -> None:
        """Set the number of times the gate is applied."""
        self._power = power
        self._mark_dirty()

    def _str_attributes(self) -> list[str]:
        """Helper method used to list the attributes of the gate for the __str__ representation."""
        strings = []
        if num_controls := self.num_controls:
            strings.append(f"numControls={num_controls}")
        if self.adjoint:
            strings.append("adjoint")
        if (power := self.power) != 1:
            strings.append(f"power={power}")
        return strings


class WellKnownGate(QubitGate):
    """A standard quantum gate.

    Well-known gates must be one of the gates defined in the spec. No additional data needs to be specified.
    """

    _kind: KnownGate

    def __init__(
        self,
        kind: KnownGate,
        *,
        num_controls: int = 0,
        adjoint: bool = False,
        power: int = 1,
    ):
        self._kind = kind
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.QubitGate.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        writer.wellKnown = self.kind
        super()._write_to_buffer(writer, string_table)

    @property
    def num_qubits(self) -> int:
        return self.kind.num_qubits

    @property
    def num_params(self) -> int:
        return self.kind.num_params

    @property
    def qualified_name(self) -> str:
        """The name of the gate, including the 'qubit.gate.' prefix."""
        return f"{self.op_kind}.{self.kind.name}"

    @property
    def kind(self) -> KnownGate:
        """The kind of gate."""
        return self._kind

    @kind.setter
    def kind(self, kind: KnownGate) -> None:
        """Set the kind of gate."""
        self._kind = kind
        self._mark_dirty()

    def __str__(self) -> str:
        attrs = [self.qualified_name] + self._str_attributes()
        return f"({', '.join(attrs)})"


class CustomGate(QubitGate):
    """Custom quantum gate.

    Custom gates are identified by a string name, and also have to provide the
    number of qubits and float parameters.
    """

    _name: str
    _num_qubits: int
    _num_params: int

    def __init__(
        self,
        name: str,
        num_qubits: int,
        num_params: int,
        *,
        num_controls: int = 0,
        adjoint: bool = False,
        power: int = 1,
    ):
        self._name = name
        self._num_qubits = num_qubits
        self._num_params = num_params
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.QubitGate.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        custom = writer.init("custom")
        custom.name = string_table.index(self.name)
        custom.numQubits = self.num_qubits
        custom.numParams = self.num_params
        super()._write_to_buffer(writer, string_table)

    @property
    def qualified_name(self) -> str:
        """The name of the gate, including the 'qubit.gate.' prefix."""
        return f"{self.op_kind}.{self.name}"

    # settable fields

    @property
    def name(self) -> str:
        if self._name is None:
            assert (
                (func := self._op._func) and (mod := func._module) and not mod.is_dirty
            ), (
                "The parent module is not present or dirty, and no name has been cached. "
                "Please call `_read_from_buffer` on the module to access this attribute."
            )

            self._name = self._op._func._module.string_table[self._raw_data.custom.name]

        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name
        self._mark_dirty()

    @property
    def num_qubits(self) -> int:
        if self._num_qubits is None:
            self._num_qubits = self._raw_data.custom.numQubits
        return self._num_qubits

    @num_qubits.setter
    def num_qubits(self, num_qubits: int) -> None:
        self._num_qubits = num_qubits
        self._mark_dirty()

    @property
    def num_params(self) -> int:
        if self._num_params is None:
            self._num_params = self._raw_data.custom.numParams
        return self._num_params

    @num_params.setter
    def num_params(self, num_params: int) -> None:
        self._num_params = num_params
        self._mark_dirty()

    # Python integration

    def __str__(self) -> str:
        strings = [f"{self.qualified_name}", f"numQubits={self.num_qubits}"]
        if numParams := self.num_params:
            strings += [f"numParams={numParams}"]
        strings += self._str_attributes()
        return f"({', '.join(strings)})"


class PPRGate(QubitGate):
    """Pauli-product rotation gate."""

    _pauli_string: list[Pauli] | None = None

    def __init__(
        self,
        pauli_string: list[Pauli | str],
        *,
        num_controls: int = 0,
        adjoint: bool = False,
        power: int = 1,
    ):
        self.pauli_string = pauli_string
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _force_read_all(self) -> None:
        _ = self.pauli_string
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.QubitGate.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        ppr = writer.init("ppr")
        _pauli_string = self.pauli_string
        pauli_string = ppr.init("pauliString", len(_pauli_string))
        for i, pauli in enumerate(_pauli_string):
            pauli_string[i] = pauli.value
        super()._write_to_buffer(writer, string_table)

    @property
    def qualified_name(self) -> str:
        """The name of the gate, including the 'qubit.gate.' prefix."""
        return f"{self.op_kind}.ppr"

    # settable fields

    @property
    def pauli_string(self) -> list[Pauli]:
        if self._pauli_string is None:
            if self._raw_data is None:
                msg = "Pauli string has not been assigned yet."
                raise ValueError(msg)
            self._pauli_string = [
                Pauli.from_name(pauli) for pauli in self._raw_data.ppr.pauliString
            ]
        return self._pauli_string

    @pauli_string.setter
    def pauli_string(self, pauli_string: list[Pauli | str]) -> None:
        self._pauli_string = [
            Pauli.from_name(p) if isinstance(p, str) else p for p in pauli_string
        ]
        self._mark_dirty()

    @property
    def num_qubits(self) -> int:
        return len(self.pauli_string)

    @property
    def num_params(self) -> int:
        return 1

    def __str__(self) -> str:
        attrs = [
            self.qualified_name,
            f"pauliString={self.pauli_string}",
        ] + self._str_attributes()
        return f"({', '.join(attrs)})"
