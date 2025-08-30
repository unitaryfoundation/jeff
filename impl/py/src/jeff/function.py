"""Function definitions and declarations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from typing_extensions import override

from jeff.op import JeffOp
from jeff.region import Region
from jeff.type import JeffType


from .capnp import CapnpBuffer, LazyUpdate, schema
from .string_table import StringTable
from .value import Value, ValueTable

if TYPE_CHECKING:
    from jeff.module import Module


class Function(ABC, CapnpBuffer[schema.Function, schema.Function.Builder], LazyUpdate):  # type: ignore
    """Function definition or declaration.

    Jeff supports both function definitions (with a body) and declarations (with a signature).
    For both the name is stored as a string attribute.
    """

    # cached attributes
    _name: str | None = None

    # The read-only buffer backing this object.
    _raw_data: schema.Function = None  # type: ignore

    # Reference to the containing module.
    _module: Module | None = None

    @override
    def _mark_dirty(self) -> None:
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = True
        if self._module:
            self._module._mark_dirty()

    @staticmethod
    def _read_from_buffer(func: schema.Function) -> Function:  # type: ignore
        """Construct a function from encoded data. This provides a zero-copy view of the data."""
        obj: Function
        match func.which:
            case "definition":
                definition = func.definition
                body = Region._read_from_buffer(definition.body)
                values = ValueTable([])
                for i, val in enumerate(definition.values):
                    val = Value._read_from_buffer(val)
                    val.id = i
                    values.add(val)

                obj = FunctionDef.__new__(FunctionDef)
                obj._body = body
                obj._value_table = values
            case "declaration":
                declaration = func.declaration
                # Declaration I/O values do not have an id, as they are not connected ports.
                inputs = [Value._read_from_buffer(val) for val in declaration.inputs]
                outputs = [Value._read_from_buffer(val) for val in declaration.outputs]
                obj = FunctionDecl.__new__(FunctionDecl)
                obj._inputs = inputs
                obj._outputs = outputs
            case _:
                raise ValueError(f"unknown function type: {func.which}")

        obj._name = None
        obj._raw_data = func
        obj._mark_clean()
        return obj

    def _force_read_all(self) -> None:
        _ = self.name
        self._raw_data = None
        self._mark_dirty()

    # settable fields

    @property
    def name(self) -> str:
        if self._name is None:
            if self._module is None:
                raise ValueError(
                    "Name hasn't been assigned yet to function without parent module"
                )
            if self._raw_data is None:
                raise ValueError("Name hasn't been assigned yet")

            idx = self._raw_data.name
            self._name = self._module.string_table[idx]

        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name
        self._mark_dirty()

    # convenience methods

    @property
    @abstractmethod
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        """Return the input/output type signature of the function."""

    @property
    def is_definition(self) -> bool:
        """Returns True if the function is a definition."""
        return isinstance(self, FunctionDef)

    @property
    def is_declaration(self) -> bool:
        """Returns True if the function is a declaration."""
        return isinstance(self, FunctionDecl)

    # Python integration

    def __str__(self) -> str:
        input_types, output_types = self.function_type

        string = f"func @{self.name}"
        string += f"({', '.join(str(ty) for ty in input_types)})"
        string += " -> "
        string += f"({', '.join(str(ty) for ty in output_types)})"

        if isinstance(self, FunctionDef):
            string += f":\n{self.body}"
        else:
            assert isinstance(self, FunctionDecl)
            string += ";"

        return string


class FunctionDef(Function):
    """Function definitions.

    Contains a single region determining the call signature of the function.
    The encoded object also contains a value table for all typed values in the program.
    """

    # The dataflow region defining this functions
    _body: Region

    # A table of typed values containing the function hyperedge types and metadata
    _value_table: ValueTable

    def __init__(self, name: str, body: Region):
        value_table = ValueTable._collect_from_region(body)
        value_table._func = self

        body._set_parent(self)

        self._name = name
        self._body = body
        self._value_table = value_table

        self._mark_dirty()

    def _force_read_all(self) -> None:
        self._body._force_read_all()
        self._value_table._force_read_all()
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.Function.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        definition = writer.init("definition")
        values = definition.init("values", len(self._value_table))
        self._value_table._write_to_buffer(values, string_table)
        self._body._write_to_buffer(definition.body, string_table)

        # strings are stored as indices in the encoded format
        writer.name = string_table.index(self.name)

        self._raw_data = writer.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def body(self) -> Region:
        return self._body

    @body.setter
    def body(self, body: Region) -> None:
        for op in body.operations:
            op._func = self
        body._parent = self
        self._body = body
        self._mark_dirty()

    @property
    def value_table(self) -> ValueTable:
        return self._value_table

    @value_table.setter
    def value_table(self, value_table: ValueTable) -> None:
        value_table._func = self
        self._value_table = value_table
        self._mark_dirty()

    # convenience methods

    @property
    def sources(self) -> list[Value]:
        return self.body.sources

    @property
    def targets(self) -> list[Value]:
        return self.body.targets

    @property
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        input_types = [inp.type for inp in self.sources]
        output_types = [out.type for out in self.targets]
        return input_types, output_types

    def __getitem__(self, idx: int) -> JeffOp:
        """Retrieve an operation in the function region by index."""
        return self.body[idx]

    def __len__(self) -> int:
        """The number of operations in the function region."""
        return len(self.body)


class FunctionDecl(Function):
    """Function declarations contain only the input/output type signature."""

    # cached attributes
    _inputs: list[Value] | None = None
    _outputs: list[Value] | None = None

    def __init__(self, name: str, inputs: list[Value], outputs: list[Value]):
        self._name = name
        self._inputs = inputs
        self._outputs = outputs
        self._mark_dirty()

    def _force_read_all(self) -> None:
        _ = self.inputs
        _ = self.outputs
        super()._force_read_all()

    def _write_to_buffer(
        self,
        writer: schema.Function.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        writer.name = self.name

        declaration = writer.init("declaration")

        _inputs = self.inputs
        inputs = declaration.init("inputs", len(_inputs))
        for i, input in enumerate(_inputs):
            input._write_to_buffer(inputs[i], string_table)

        _outputs = self.outputs
        outputs = declaration.init("outputs", len(_outputs))
        for i, output in enumerate(_outputs):
            output._write_to_buffer(outputs[i], string_table)

        # strings are stored as indices in the encoded format
        writer.name = string_table.index(self.name)

        self._raw_data = writer.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def inputs(self) -> list[Value]:
        if self._inputs is None:
            self._inputs = [
                Value._read_from_buffer(inp)
                for inp in self._raw_data.declaration.inputs
            ]
        return self._inputs

    @inputs.setter
    def inputs(self, inputs: list[Value]) -> None:
        self._inputs = inputs
        self._mark_dirty()

    @property
    def outputs(self) -> list[Value]:
        if self._outputs is None:
            self._outputs = [
                Value._read_from_buffer(out)
                for out in self._raw_data.declaration.outputs
            ]
        return self._outputs

    @outputs.setter
    def outputs(self, outputs: list[Value]) -> None:
        self._outputs = outputs
        self._mark_dirty()

    # convenience methods

    @property
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        input_types = [inp.type for inp in self.inputs]
        output_types = [out.type for out in self.outputs]
        return input_types, output_types
