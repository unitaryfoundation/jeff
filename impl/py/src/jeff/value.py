"""Values identifying typed hyperedges in the program."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
from typing_extensions import override

from .capnp import schema, CapnpBuffer, LazyUpdate
from .type import JeffType
from .string_table import StringTable

if TYPE_CHECKING:
    from jeff.function import FunctionDef
    from jeff.region import Region


# TODO: What's the correct type for capnp list[schema.Value] reader and writers?
class ValueTable(CapnpBuffer[Any, Any], LazyUpdate):
    """An indexed value table."""

    _value_table: dict[int, Value]
    _len = 0

    # TODO: Not the correct type. What's the type of a capnp list reader?
    _raw_data: Any | None = None

    # A reference to the function definition defining this value table
    _func: FunctionDef | None = None

    def __init__(self, value_table: list[Value]):
        self._value_table = {i: s for i, s in enumerate(value_table)}
        self._len = len(value_table)
        self._mark_dirty()

    @staticmethod
    def _collect_from_region(region: Region) -> ValueTable:
        """Compute a value table from a region.

        Traverses the region and its operations collecting any value defined in it,
        adds them to a value table and sets the ids for each value.
        """
        # The value table to return
        table = ValueTable([])

        # Values which already have an id
        value_dict: dict[int, Value] = {}
        # Values which have not yet been assigned an id
        unordered_values: deque[Value] = deque()

        def add_value(val: Value) -> None:
            val._value_table = table
            match val.id:
                case None:
                    unordered_values.append(val)
                case id:
                    value_dict[id] = val

        for region in region.subregions_bfs():
            for val in region.sources + region.targets:
                add_value(val)

            for op in region:
                for val in op.inputs + op.outputs:
                    add_value(val)

        # Assign ids to all values
        taken_ids = deque(sorted(value_dict.keys()))
        id = 0
        while unordered_values or taken_ids:
            table._len = max(id + 1, table._len)
            if id in value_dict:
                table[id] = value_dict[id]
            elif unordered_values:
                val = unordered_values.popleft()
                val.id = id
                table[id] = val
            # Bump the next assignable id
            if not unordered_values and taken_ids:
                id = taken_ids.popleft()
            else:
                id += 1

        return table

    @override
    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._func:
            self._func._mark_dirty()

    @staticmethod
    def _read_from_buffer(reader: Any) -> ValueTable:
        # Do not read the values eagerly, only fetch them when needed.
        table = ValueTable([])
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
            self[i]._write_to_buffer(writer[i], string_table)
        self._raw_data = writer.as_reader()
        self._mark_clean()

    def add(self, value: Value) -> int:
        """Add a value to the value table and return its id.

        If the value already has an id matching an existing entry,
        checks that the types and metadata coincide.

        :returns: The id of the added value.
        :raises ValueError: If the table already contains a different value with the same id.
        """
        value._value_table = self
        if value.id is None:
            id = self._len
            value.id = id
            self._value_table[id] = value
            self._len += 1
            self._mark_dirty()
            return id

        if value.id not in self._value_table:
            self._value_table[value.id] = value
            self._len = max(self._len, value.id + 1)
            self._mark_dirty()
            return value.id

        if self._value_table[value.id] != value:
            raise ValueError(
                f"Value #{value} already exists in value table with type {self._value_table[value.id].type}"
            )

        return value.id

    def __getitem__(self, index: int) -> Value:
        if index < 0 or index >= self._len:
            msg = f"Index {index} is out of bounds for value table with {self._len} values"
            raise IndexError(msg)
        if index not in self._value_table:
            if self._raw_data is None:
                msg = (
                    f"Value table is incomplete. id {index} has not been assigned yet."
                )
                raise ValueError(msg)
            value_reader = self._raw_data.index(index)
            val = Value._read_from_buffer(value_reader)
            val.id = index
            val._value_table = self
            self._value_table[index] = val
        return self._value_table[index]

    def __setitem__(self, index: int, value: Value) -> None:
        value.id = index
        value._value_table = self

        self._value_table[index] = value
        if index >= self._len:
            self._len = index + 1
        self._mark_dirty()

    def __len__(self) -> int:
        return self._len


@dataclass
class Value(CapnpBuffer[schema.Value, schema.Value.Builder]):  # type: ignore
    """Program values represent dataflow between operations, and defines the data type used.

    This class is immutable, and holds an identifier for the unique edge in the program. In an
    encoded program, the identifier is the index into the parent function's value table, whereas
    during program construction the identifier is the object's instance id.

    :attr id: The value table index or `None` if not yet assigned.
    :attr type: The type of the value.
    """

    # The value table index is used in reader mode both for pretty printing and comparing values.
    type: JeffType
    id: int | None = None

    # TODO: Add register metadata

    # The value table that defines this value with id `self.id`, if available.
    _value_table: ValueTable | None = None

    @staticmethod
    def _read_from_buffer(reader: schema.Value) -> Value:  # type: ignore
        type = JeffType._read_from_buffer(reader.type)
        return Value(type)

    def _force_read_all(self) -> None:
        pass

    def _write_to_buffer(
        self,
        new_data: schema.Value.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        # For immutable classes, just write the cached data into the encoding buffer.
        self.type._write_to_buffer(new_data.type, string_table)

    def __str__(self) -> str:
        if self.id is None:
            return f"%{self.type}"
        else:
            return f"%{self.id}:{self.type}"
