"""Common protocol definition for all quantum operations"""

from typing import Protocol

from jeff.capnp import Builder, Reader
from jeff.op.kind import OpType


class QubitOp(Protocol, OpType[Reader, Builder]):
    """A qubit operation."""
