"""An indexed string table."""

from __future__ import annotations
from typing import Any, TYPE_CHECKING, override

from jeff.capnp import CapnpBuffer, LazyUpdate

if TYPE_CHECKING:
    from jeff.module import Module
    from jeff.function import FunctionDef


# TODO: What's the correct type for capnp list[str] reader and writers?
class StringTable(CapnpBuffer[Any, Any], LazyUpdate):
    """An indexed string table.

    Lazy-loaded from a capnp string list buffer.
    """

    # Cached sparse list of strings.
    # This may contain holes, but all indices will be below `self._len`
    _string_table: dict[int, str]
    # Reverse mapping from string to index
    _reverse_table: dict[str, int]
    # The number of elements in the table
    _len = 0

    # The buffer backing this list
    _raw_data: Any | None = None

    # A reference to the module defining this table.
    _module: Module | None = None

    def __init__(self, string_table: list[str]):
        self._string_table = {i: s for i, s in enumerate(string_table)}
        self._reverse_table = {s: i for i, s in enumerate(string_table)}
        self._len = len(string_table)
        self._mark_dirty()

    def _update_with_function(self, function: FunctionDef) -> None:
        """Collect all the strings used in a function and update the table.

        Traverses the function operations and  and its operations collecting any value defined in it,
        adds them to a value table and sets the ids for each value.
        """
        from jeff.op.qubit import CustomGate

        self.insert(function.name)

        for region in function.body.subregions_bfs():
            for op in region:
                if isinstance(op.op_type, CustomGate):
                    self.insert(op.op_type.name)

            # TODO: Add metadata keys too, once we support them

    @override
    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._module:
            self._module._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: Any) -> StringTable:
        # Do not read the strings eagerly, only fetch them when needed.
        table = StringTable([])
        table._raw_data = reader
        table._len = reader.len
        table._mark_clean()
        return table

    def _force_read_all(self) -> None:
        for i in range(len(self)):
            self[i]
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: Any,
        string_table: StringTable,
    ) -> None:
        for i in range(self._len):
            writer[i] = self[i]
        self._raw_data = writer.as_reader()
        self._mark_clean()

    def index(self, value: str) -> int:
        """Returns the index of a string in the table."""
        return self._reverse_table[value]

    def insert(self, value: str) -> int:
        """Inserts a string into the table and returns its index."""
        if value in self._reverse_table:
            return self._reverse_table[value]
        index = self._len
        self[index] = value
        return index

    def __len__(self) -> int:
        return self._len

    def __getitem__(self, index: int) -> str:
        if index < 0 or index >= self._len:
            msg = f"Index {index} is out of bounds for string table with {self._len} strings"
            raise IndexError(msg)
        if index not in self._string_table:
            if self._raw_data is None:
                msg = f"String table is incomplete. index {index} has not been assigned yet."
                raise ValueError(msg)
            s = self._raw_data.index(index)
            self._string_table[index] = s
            self._reverse_table[s] = index
        return self._string_table[index]

    def __setitem__(self, index: int, value: str) -> None:
        self._string_table[index] = value
        self._reverse_table[value] = index
        if index >= self._len:
            self._len = index + 1
        self._mark_dirty()
