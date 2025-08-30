"""Top-level module definition."""

from __future__ import annotations
from typing import Iterator

from jeff.function import Function, FunctionDef

from .capnp import CapnpBuffer, LazyUpdate, schema
from .string_table import StringTable


class Module(CapnpBuffer[schema.Module, schema.Module.Builder], LazyUpdate):  # type: ignore
    """Jeff module.

    The module is the root node in the program. It's a container for functions,
    as well as certain metadata. The encoded object also stores a string table
    for all string attributes in the program.

    :attr functions: The functions in the module.
    :attr entrypoint: The index of the entrypoint function in the `functions` list.
    :attr version: The version of the *jeff* format used to encode this module.
    :attr tool: The name of the tool that generated this module.
    :attr tool_version: The version of the tool that generated this module.
    :attr string_table: The string table for all string attributes in the program.
    """

    _raw_data: schema.Module = None  # type: ignore

    # Cached list of functions in the module, indexed by their id.
    # These are loaded lazily individually.
    _functions: dict[int, Function]
    _function_count: int

    # Index of the entrypoint function in the `functions` list.
    _entrypoint: int

    # Version of the *jeff* format used to encode this module.
    _version: int

    # Name of the tool that generated this module.
    _tool: str

    # Version of the tool that generated this module.
    _tool_version: str

    # String table for all string attributes in the program.
    _string_table: StringTable

    def __init__(
        self,
        functions: list[Function],
        *,
        entrypoint: int = 0,
        version: int = 0,
        tool: str | None = None,
        tool_version: str | None = None,
    ):
        self._string_table = StringTable([])

        if tool is None or tool_version is None:
            from jeff import __version__ as jeff_version

            tool = "jeff-py"
            tool_version = jeff_version

        for func in functions:
            func._module = self
            if isinstance(func, FunctionDef):
                self._string_table._update_with_function(func)

        self.functions = functions
        self._entrypoint = entrypoint
        self._version = version
        self._tool = tool
        self._tool_version = tool_version
        self._mark_dirty()

    def refresh(self) -> None:
        """Refresh this object's encoded data with cached modifications.

        Also refreshes all child objects. This method guarantees that `is_dirty`
        is False after invocation, and When is `is_dirty` is already False, this
        method does nothing.
        """
        if not self.is_dirty:
            return

        # Reusing an existing message is a bad idea as any new allocations will leave the old ones
        # in the message, bloating its size.
        new_data = schema.Module.new_message()  # type: ignore
        string_table = self._string_table
        self._write_to_buffer(new_data, string_table)

    def write_out(self, path: str) -> None:
        """Write out the program to file. Only available on the module object as the root node.
        Automatically calls `refresh` before writing.
        """
        self.refresh()

        with open(path, "wb") as f:
            self._raw_data.write(f)

    @staticmethod
    def _read_from_buffer(module: schema.Module) -> Module:  # type: ignore
        """Construct a JeffModule from encoded data. This provides a zero-copy view of the data."""
        obj = Module.__new__(Module)
        obj._raw_data = module
        obj._function_count = len(module.functions)
        obj._entrypoint = module.entrypoint
        obj._version = module.version
        obj._tool = module.tool
        obj._tool_version = module.toolVersion
        obj._string_table = StringTable._read_from_buffer(module.strings)
        obj._mark_clean()
        return obj

    def _force_read_all(self) -> None:
        """Force the object to read all the data from the buffer into memory,
        and drop any internal references to a Reader.

        This is useful when transitioning an object from "reader" mode to "writer" mode.

        This call spreads recursively to all child objects.
        """
        for func in self.functions:
            func._force_read_all()
        self._raw_data = None
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.Module.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        functions = writer.init("functions", len(self._functions))
        for i in range(len(self._functions)):
            self[i]._write_to_buffer(functions[i], string_table)

        writer.entrypoint = self.entrypoint
        writer.version = self.version
        writer.tool = self.tool
        writer.toolVersion = self.tool_version

        strings = writer.init("strings", len(string_table))
        string_table._write_to_buffer(strings, string_table)

        self._raw_data = writer.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def functions(self) -> list[Function]:
        """Returns a list of functions in the module."""
        return list(self)

    @functions.setter
    def functions(self, functions: list[Function]) -> None:
        """Set the functions in the module."""
        for func in functions:
            # "adopting" a read-only object will detach it from its original encoded message,
            # so let's load any data associated to it into cache
            func._force_read_all()
            func._module = self
            if isinstance(func, FunctionDef):
                self._string_table._update_with_function(func)
        self._functions = {i: func for i, func in enumerate(functions)}
        self._function_count = len(functions)
        self._mark_dirty()

    # encoding-only fields

    @property
    def string_table(self) -> StringTable:
        """The string table for all string attributes in the program."""
        return self._string_table

    # static fields

    @property
    def entrypoint(self) -> int:
        """The index of the entrypoint function in the `functions` list."""
        return self._entrypoint

    @property
    def version(self) -> int:
        """The version of the *jeff* format used to encode this module."""
        return self._version

    @property
    def tool(self) -> str:
        """The name of the tool that generated this module."""
        return self._tool

    @property
    def tool_version(self) -> str:
        """The version of the tool that generated this module."""
        return self._tool_version

    def __getitem__(self, idx: int) -> Function:
        """Returns the function at the given index."""
        if idx < 0 or idx >= self._function_count:
            raise IndexError(
                f"Index {idx} is out of bounds for module with {self._function_count} functions"
            )
        if idx not in self._functions:
            if self._raw_data is None:
                msg = f"Module is incomplete. function {idx} has not been assigned yet."
                raise ValueError(msg)
            func = Function._read_from_buffer(self._raw_data.functions[idx])
            func._module = self
            self._functions[idx] = func
        return self._functions[idx]

    def __setitem__(self, idx: int, func: Function) -> None:
        """Set the function at the given index.

        :raises: If idx is equal or larger than `len(self)`.
        """
        if idx < 0 or idx >= self._function_count:
            raise IndexError(
                f"Index {idx} is out of bounds for module with {self._function_count} functions"
            )
        func._module = self
        self._functions[idx] = func
        self._mark_dirty()

    def __len__(self) -> int:
        """The number of functions in the module."""
        return self._function_count

    def __iter__(self) -> Iterator[Function]:
        for i in range(len(self)):
            yield self[i]

    def __str__(self) -> str:
        string = f"jeff v{self.version}"

        if self.tool:
            string += f", {self.tool} v{self.tool_version}"
        string += "\n\n"

        for i, func in enumerate(self):
            string += f"{'[entry] ' if i == self.entrypoint else ''}{func}\n"

        return string
