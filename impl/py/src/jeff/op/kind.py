"""Operation kinds."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol

from jeff.capnp import Builder, CapnpBuffer, Reader

if TYPE_CHECKING:
    from jeff.op import JeffOp


class OpKind(Enum):
    """Categories of operation types.

    Each of these are represented by different classes in the API.
    They roughly correspond to structs in the capnp schema.
    """

    QUBIT = "qubit"
    QUBIT_GATE = "qubit.gate"
    SCF = "scf"

    @property
    def kind(self) -> str:
        """The kind of operation."""
        return self.value.split(".")[0]

    @property
    def subkind(self) -> str | None:
        """The subkind of operation, if any."""
        if "." not in self.value:
            return None
        return self.value.split(".")[1]


class OpType(Protocol, CapnpBuffer[Reader, Builder]):
    """A concrete jeff operation type."""

    # Reference to the containing operation.
    _op: JeffOp | None = None

    @property
    def op_kind(self) -> OpKind:
        """The kind of operation."""
