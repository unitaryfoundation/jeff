"""Non unitary qubit operations"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import override

from jeff.capnp import LazyUpdate, schema
from jeff.string_table import StringTable
from jeff.op.kind import OpKind
from jeff.op.qubit.protocol import QubitOp


class NonUnitaryOp(
    ABC,
    QubitOp[schema.QubitOp, schema.QubitGate.Builder],  # type: ignore
    LazyUpdate,
):
    """A non-unitary quantum operation.

    See QubitGate for unitary operations.
    """

    # The read-only buffer backing this object.
    _raw_data: schema.QubitOp | None = None  # type: ignore

    @override
    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._op:
            self._op._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: schema.QubitOp) -> NonUnitaryOp:  # type: ignore
        ops = [
            QubitAlloc(),
            QubitFree(),
            QubitFreeZero(),
            QubitMeasure(),
            QubitMeasureNd(),
            QubitReset(),
        ]
        which = reader.which
        for op in ops:
            if op.name == which:
                return op
        else:
            raise ValueError(f"unknown gate type: {reader.which}")

    def _force_read_all(self) -> None:
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.QubitGate.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        # Setting the op variant to `None` marks it as the current value.
        setattr(writer, self.name, None)
        self._raw_data = writer.as_reader()
        self._mark_clean()

    @property
    def op_kind(self) -> OpKind:
        """The kind of operation."""
        return OpKind.QUBIT

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the operation"""

    @property
    def qualified_name(self) -> str:
        """Full name of the operation, including the "qubit." prefix"""
        return f"{self.op_kind}.{self.name}"

    def __str__(self) -> str:
        return self.qualified_name


class QubitAlloc(NonUnitaryOp):
    """Allocates a new qubit in the |0> state.

    Outputs:
    - `qubit`: The newly allocated qubit.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "alloc"


class QubitFree(NonUnitaryOp):
    """Frees a qubit.

    This operation makes no assumptions about the state of the qubit.

    Inputs:
    - `qubit`: The qubit to free.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "free"


class QubitFreeZero(NonUnitaryOp):
    """Frees a qubit in the |0> state.

    This operation can be used to avoid performing resets when it is known
    that the qubit has already been reset. It is undefined behavior to free
    a qubit that is not in the |0> state.

    Inputs:
    - `qubit`: The qubit to free.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "freeZero"


class QubitMeasure(NonUnitaryOp):
    """Perform a destructive measurement of a qubit in the computational basis.

    Inputs:
    - `qubit`: The qubit to measure.

    Outputs:
    - `int(1)`: The measurement result.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "measure"


class QubitMeasureNd(NonUnitaryOp):
    """Perform a non-destructive measurement of a qubit in the computational basis.

    Inputs:
    - `qubit`: The qubit to measure.

    Outputs:
    - `qubit`: The measured qubit.
    - `int(1)`: The measurement result.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "measureNd"


class QubitReset(NonUnitaryOp):
    """Resets a qubit to the |0> state.

    Inputs:
    - `qubit`: The qubit to reset.

    Outputs:
    - `qubit`: The reset qubit.
    """

    @property
    def name(self) -> str:
        """Name of the operation"""
        return "reset"
