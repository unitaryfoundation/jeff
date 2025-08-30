"""Dataflow regions."""

from __future__ import annotations

from collections import deque
import textwrap
from typing import TYPE_CHECKING, Iterator
from typing_extensions import override

from .capnp import CapnpBuffer, LazyUpdate, schema
from .string_table import StringTable
from .value import Value

if TYPE_CHECKING:
    from .op import JeffOp
    from .op.scf import Scf
    from .function import FunctionDef


class Region(CapnpBuffer[schema.Region, schema.Region.Builder], LazyUpdate):  # type: ignore
    """A region is container for operations, and defines input and output ports. Regions do not
    allow value edges across it."""

    # cached attributes
    _sources: list[Value] | None = None
    _targets: list[Value] | None = None

    # The list of operations in this region, indexed by their id.
    # We lazily load each one individually.
    _operations: dict[int, JeffOp]
    _operation_count: int

    # The read-only buffer backing this object.
    _raw_data: schema.Region | None = None  # type: ignore

    # Reference to the containing function or scf.
    _parent: FunctionDef | Scf | None = None

    def __init__(
        self,
        sources: list[Value],
        targets: list[Value],
        operations: list[JeffOp],
    ):
        self._sources = sources
        self._targets = targets
        self.operations = operations
        self._mark_dirty()

    @override
    def _mark_dirty(self) -> None:
        self._is_dirty = True
        if self._parent:
            self._parent._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: schema.Region) -> Region:  # type: ignore
        region = Region.__new__(Region)
        region._raw_data = reader
        region._operation_count = len(reader.operations)
        region._mark_clean()
        return region

    def _force_read_all(self) -> None:
        _ = self.sources
        _ = self.targets
        _ = self.operations
        for op in self._operations.values():
            op._force_read_all()
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.Region.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        _sources = self.sources
        sources = writer.init("sources", len(_sources))
        for i, val in enumerate(_sources):
            sources[i] = val.id

        _targets = self.targets
        targets = writer.init("targets", len(_targets))
        for i, val in enumerate(_targets):
            targets[i] = val.id

        ops_writer = writer.init("operations", self._operation_count)
        for i in range(self._operation_count):
            op = self[i]
            op._write_to_buffer(ops_writer[i], string_table)

        self._raw_data = writer.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def sources(self) -> list[Value]:
        if self._sources is None:
            if self.parent_func is None:
                raise ValueError(
                    "Source values haven't been assigned yet to region without parent function"
                )
            if self._raw_data is None:
                raise ValueError("Source values haven't been assigned yet")
            self._sources = []
            for source_id in self._raw_data.sources:
                val = self.parent_func.value_table[source_id]
                self._sources.append(val)
        return self._sources

    @sources.setter
    def sources(self, sources: list[Value]) -> None:
        if self.parent_func is not None:
            for val in sources:
                self.parent_func.value_table.add(val)
        self._sources = sources
        self._mark_dirty()

    @property
    def targets(self) -> list[Value]:
        if self._targets is None:
            if self.parent_func is None:
                raise ValueError(
                    "Target values haven't been assigned yet to region without parent function"
                )
            if self._raw_data is None:
                raise ValueError("Target values haven't been assigned yet")
            self._targets = []
            for target_id in self._raw_data.targets:
                val = self.parent_func.value_table[target_id]
                self._targets.append(val)
        return self._targets

    @targets.setter
    def targets(self, targets: list[Value]) -> None:
        if self.parent_func is not None:
            for val in targets:
                self.parent_func.value_table.add(val)
        self._targets = targets
        self._mark_dirty()

    @property
    def operations(self) -> list[JeffOp]:
        """A copy of the list of operations in the region"""
        return list(self)

    @operations.setter
    def operations(self, operations: list[JeffOp]) -> None:
        if (func := self.parent_func) is not None:
            for op in operations:
                op._func = func
        self._operations = {i: op for i, op in enumerate(operations)}
        self._operation_count = len(operations)
        self._mark_dirty()

    def append_op(self, op: JeffOp) -> int:
        """Append an operation to the region.

        :returns: The index of the new operation.
        """
        if (func := self.parent_func) is not None:
            op._func = func
        idx = self._operation_count
        self._operations[idx] = op
        self._operation_count += 1
        self._mark_dirty()
        return idx

    # convenience methods

    @property
    def parent_func(self) -> FunctionDef | None:
        """Returns the parent function to this region, if any."""
        match self._parent:
            case FunctionDef():
                return self._parent
            case Scf():
                return self._parent.parent_func
            case _:
                return None

    def _set_parent(self, parent: FunctionDef | Scf) -> None:
        """Set the parent container of this region.

        This may be either a function if this is a top-level region in the definition,
        or a scf if this is region is nested.
        """
        self._parent = parent
        if (func := self.parent_func) is not None:
            for op in self._operations.values():
                op._func = func
            for val in self.sources + self.targets:
                func.value_table.add(val)

    def subregions_bfs(self) -> Iterator[Region]:
        """Returns an iterator over all the subregions in this region, in breadth-first order.

        The iterator returns the region itself first, then all its subregions, then all their
        subregions, and so on.
        """
        from jeff.op.scf import SwitchSCF, ForSCF, WhileSCF, DoWhileSCF

        queue = deque([self])
        while region := queue.popleft():
            yield region

            for op in region:
                match op.op_type:
                    case SwitchSCF():
                        for branch in op.op_type.branches:
                            queue.append(branch)
                        if op.op_type.default:
                            queue.append(op.op_type.default)
                    case ForSCF():
                        queue.append(op.op_type.body)
                    case WhileSCF() | DoWhileSCF():
                        queue.append(op.op_type.condition)
                        queue.append(op.op_type.body)
                    case _:
                        pass

    # Python integration

    def __getitem__(self, idx: int) -> JeffOp:
        """Retrieve an operation in the region by index."""
        if idx < 0 or idx >= self._operation_count:
            raise IndexError(
                f"Index {idx} is out of bounds for region with {self._operation_count} operations"
            )
        if idx not in self._operations:
            if self._raw_data is None:
                msg = (
                    f"Region is incomplete. operation {idx} has not been assigned yet."
                )
                raise ValueError(msg)
            op = JeffOp._read_from_buffer(self._raw_data.operations[idx])
            if (func := self.parent_func) is not None:
                op._func = func
            self._operations[idx] = op
        return self._operations[idx]

    def __setitem__(self, idx: int, op: JeffOp) -> None:
        """Set the value of an operation in the function

        :raises: If idx is equal or larger than `len(self)`.
        """
        if idx >= self._operation_count:
            msg = f"Index {idx} is out of bounds for region with {self._operation_count} operations"
            raise IndexError(msg)
        if (func := self.parent_func) is not None:
            op._func = func
        self._operations[idx] = op
        self._mark_dirty()

    def __len__(self) -> int:
        """The number of operations in the region."""
        return self._operation_count

    def __iter__(self) -> Iterator[JeffOp]:
        for i in range(len(self)):
            yield self[i]

    def __str__(self) -> str:
        string = ""

        string += "  in :"
        if sources := self.sources:
            string += f" {', '.join(str(src) for src in sources)}"
        string += "\n"

        for op in self:
            string += f"{textwrap.indent(str(op), '    ')}\n"

        string += "  out:"
        if targets := self.targets:
            string += f" {', '.join(str(tgt) for tgt in targets)}"
        string += ""

        return string
