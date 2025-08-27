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
"""

from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod
from typing import Any, Iterable

# from .capnp import load_schema

# TODO: Temporarily disabled
# schema = load_schema()
schema = None

# TODO: add remaining op instructions
# TODO: add methods to convert read-only data to cached (builder) instances, remove '_update_cache'
# TODO: introduce JeffString to reduce reliance on string table searching?
# TODO: parent field propagation (like '_func', '_parent', etc.) could be improved
# TODO: add metadata support

#########
# Enums #
#########

FloatPrecisions = (32, 64)

Paulis = ("i", "x", "y", "z")

KnownGates = (
    "gphase",
    "i",
    "x",
    "y",
    "z",
    "s",
    "t",
    "r1",
    "rx",
    "ry",
    "rz",
    "h",
    "u",
    "swap",
)

################
# Core classes #
################


class _Empty:
    """Sentinal value for uninitialized fields."""


class JeffType(ABC):
    """Type information for values. This class is immutable.
    Some types carry additional data like a bitwidth."""

    _raw_data: schema.Type = None

    @staticmethod
    def from_encoding(type: schema.Type):
        cls = {
            "qubit": QubitType,
            "qureg": QuregType,
            "int": IntType,
            "intArray": IntArrayType,
            "float": FloatType,
            "floatArray": FloatArrayType,
        }[str(type.which)]
        obj = cls.__new__(cls)
        obj._raw_data = type
        return obj

    # Python integration

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if hasattr(self, "bitwidth"):
            return self.bitwidth == other.bitwidth

        return True


class QubitType(JeffType):
    """Specialization of the JeffType for qubit values."""

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.qubit = None
        self._raw_data = new_data.as_reader()

    # Python integration

    def __str__(self) -> str:
        return "qubit"


class QuregType(JeffType):
    """Specialization of the JeffType for qureg values."""

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.qureg = None
        self._raw_data = new_data.as_reader()

    # Python integration

    def __str__(self) -> str:
        return "qureg"


class IntType(JeffType):
    """Specialization of the JeffType for integer values."""

    _bitwidth: int = _Empty

    def __init__(self, bitwidth: int):
        self._bitwidth = bitwidth

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.int = self.bitwidth
        self._raw_data = new_data.as_reader()

    # static fields

    @property
    def bitwidth(self) -> int:
        if self._bitwidth is not _Empty:
            return self._bitwidth

        return self._raw_data.int

    # Python integration

    def __str__(self) -> str:
        return f"int{self.bitwidth}"


class IntArrayType(JeffType):
    """Specialization of the JeffType for integer arrays."""

    _bitwidth: int = _Empty

    def __init__(self, bitwidth: int):
        self._bitwidth = bitwidth

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.intArray = self.bitwidth
        self._raw_data = new_data.as_reader()

    # static fields

    @property
    def bitwidth(self) -> int:
        if self._bitwidth is not _Empty:
            return self._bitwidth

        return self._raw_data.intArray

    # Python integration

    def __str__(self) -> str:
        return f"int{self._bitwidth}[]"


class FloatType(JeffType):
    """Specialization of the JeffType for floating point values."""

    _bitwidth: int = _Empty

    def __init__(self, bitwidth: int):
        assert bitwidth in FloatPrecisions
        self._bitwidth = bitwidth

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.float = f"float{self.bitwidth}"
        self._raw_data = new_data.as_reader()

    # static fields

    @property
    def bitwidth(self) -> int:
        if self._bitwidth is not _Empty:
            return self._bitwidth

        return 32 if self._raw_data.float == "float32" else 64

    # Python integration

    def __str__(self) -> str:
        return f"float{self.bitwidth}"


class FloatArrayType(JeffType):
    """Specialization of the JeffType for floating point arrays."""

    _bitwidth: int = _Empty

    def __init__(self, bitwidth: int):
        assert bitwidth in FloatPrecisions
        self._bitwidth = bitwidth

    def _refresh(self, new_data: schema.Type.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        new_data.floatArray = f"float{self.bitwidth}"
        self._raw_data = new_data.as_reader()

    # static fields

    @property
    def bitwidth(self) -> int:
        if self._bitwidth is not _Empty:
            return self._bitwidth

        return 32 if self._raw_data.floatArray == "float32" else 64

    # Python integration

    def __str__(self) -> str:
        return f"float{self.bitwidth}[]"


class JeffValue:
    """Program values represent dataflow between oprations, and defines the data type used.
    This class is immutable, and holds an indentifier for the unique edge in the program. In an
    encoded program, the indentifier is the index into the parent function's value table, whereas
    during program consrtruction the identifier is the object's instance id.
    """

    _raw_data: schema.Value = None
    _func: FunctionDef = None
    # The value table index is used in reader mode both for pretty printing and comparing values.
    _val_idx: int = None

    # cached attributes
    _type: JeffType = _Empty

    def __init__(self, type: JeffType):
        self._type = type

    @staticmethod
    def from_encoding(idx: int, func: FunctionDef):
        obj = JeffValue.__new__(JeffValue)
        obj._raw_data = func._raw_data.definition.values[idx]
        obj._func = func
        obj._val_idx = idx
        return obj

    def _refresh(self, new_data: schema.Value.Builder):
        """For immutable classes, just write the cached data into the encoding buffer."""
        self.type._refresh(new_data.type)
        self._raw_data = new_data.as_reader()

    # static attributes

    @property
    def type(self):
        if self._type is not _Empty:
            return self._type

        return JeffType.from_encoding(self._raw_data.type)

    # convenience methods

    @property
    def id(self) -> int:
        if self._val_idx is not None:
            return self._val_idx

        return id(self)

    # Python integration

    def __str__(self):
        return f"%{self.id}:{self.type}"

    def __eq__(self, other):
        if not isinstance(other, JeffValue):
            return False

        if self._val_idx is not None:
            return self._func is other._func and self._val_idx == other._val_idx

        return self is other


class JeffOp:
    """A generic container for all operations in the program. The common fields include input and
    output values, as well as the kind of operation represented. All ops have a main kind
    (like QubitOp and IntOp), as well as a subkind (like alloc, add, etc.). Some operations store
    additional data as well, which can be primitive types as well extra classes defined in the API.
    """

    _is_dirty: bool
    _raw_data: schema.Op = None
    _func: FunctionDef = None

    # cached attributes
    _kind: str = _Empty
    _subkind: str = _Empty
    _inputs: list[JeffValue] = _Empty
    _outputs: list[JeffValue] = _Empty
    _instruction_data: JeffGate | JeffSCF | Any | None = _Empty

    def __init__(
        self,
        kind: str,
        subkind: str,
        inputs: list[JeffValue],
        outputs: list[JeffValue],
        instruction_data=None,
    ):
        self._kind = kind
        self._subkind = subkind
        self._inputs = inputs
        self._outputs = outputs
        if isinstance(instruction_data, (JeffGate, JeffSCF)):
            instruction_data._op = self
        self._instruction_data = instruction_data
        self._mark_dirty()

    @staticmethod
    def from_encoding(op: schema.Op, func: FunctionDef):
        obj = JeffOp.__new__(JeffOp)
        obj._raw_data = op
        obj._func = func
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self) -> bool:
        """Whether the object has been modified since the last time it was encoded. Also returns
        True if the object has never been written out (e.g. after instantiation)."""
        return self._is_dirty

    def _mark_clean(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = False

    def _mark_dirty(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = True
        if self._func:
            self._func._mark_dirty()

    def _refresh(self, new_data: schema.Op.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """

        _inputs = self.inputs
        inputs = new_data.init("inputs", len(_inputs))
        for i, val in enumerate(_inputs):
            inputs[i] = val._val_idx  # no need to search the value table

        _ouputs = self.outputs
        outptus = new_data.init("outputs", len(_ouputs))
        for i, val in enumerate(_ouputs):
            outptus[i] = val._val_idx

        instruction_group = new_data.instruction.init(self.kind)

        _data = self.instruction_data
        if isinstance(_data, JeffGate):
            gate = instruction_group.init("gate")
            _data._refresh(gate, string_table)
        elif isinstance(_data, JeffSCF):
            _data._refresh(instruction_group, string_table)
        else:  # TODO: array ops might need different initialization due to lists
            setattr(instruction_group, self.subkind, _data)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._instruction_data = self.instruction_data
        if isinstance(self._instruction_data, (JeffGate, JeffSCF)):
            self._instruction_data._update_cache()

    # cached fields

    @property
    def inputs(self) -> list[JeffValue]:
        if self._inputs is not _Empty:
            return self._inputs

        return [
            JeffValue.from_encoding(inp, self._func) for inp in self._raw_data.inputs
        ]

    @inputs.setter
    def inputs(self, inputs: list[JeffValue]):
        self._inputs = inputs
        self._mark_dirty()

    @property
    def outputs(self) -> list[JeffValue]:
        if self._outputs is not _Empty:
            return self._outputs

        return [
            JeffValue.from_encoding(out, self._func) for out in self._raw_data.outputs
        ]

    @outputs.setter
    def outputs(self, outputs: list[JeffValue]):
        self._outputs = outputs
        self._mark_dirty()

    @property
    def instruction_data(self) -> JeffGate | JeffSCF | Any | None:
        """Get instruction details if they exist. Sometimes this is basic data, othertimes another class."""
        if self._instruction_data is not _Empty:
            return self._instruction_data

        if self.kind == "qubit" and self.subkind == "gate":
            gate = self._raw_data.instruction.qubit.gate
            return JeffGate.from_encoding(gate, self)
        elif self.kind == "scf":
            scf = self._raw_data.instruction.scf
            return JeffSCF.from_encoding(scf, self)

        return getattr(getattr(self._raw_data.instruction, self.kind), self.subkind)

    @instruction_data.setter
    def instruction_data(self, data):
        if isinstance(data, (JeffGate, JeffSCF)):
            data._op = self
        self._instruction_data = data

        self._mark_dirty()

    # static fields

    @property
    def kind(self) -> str:
        if self._kind is not _Empty:
            return self._kind

        return str(self._raw_data.instruction.which)

    @property
    def subkind(self) -> str:
        if self._subkind is not _Empty:
            return self._subkind

        return str(getattr(self._raw_data.instruction, self.kind).which)

    # convenience methods

    @property
    def instruction_name(self) -> str:
        return f"{self.kind}.{self.subkind}"

    # Python integrations

    def __str__(self):
        string = ""

        if outputs := self.outputs:
            string += ", ".join(str(out) for out in outputs)
            string += " = "

        string += f"{self.instruction_name} "

        string += ", ".join(str(inp) for inp in self.inputs)

        if (data := self.instruction_data) is not None:
            string += f" {data}"

        return string


class JeffRegion:
    """A region is container for operations, and defines input and output ports. Regions do not
    allow value edges across it."""

    _is_dirty: bool
    _raw_data: schema.Region = None
    _parent: FunctionDef | JeffSCF = None

    # cached attributes
    _sources: list[JeffValue] = _Empty
    _targets: list[JeffValue] = _Empty
    _operations: list[JeffOp] = _Empty

    def __init__(
        self,
        sources: list[JeffValue],
        targets: list[JeffValue],
        operations: list[JeffOp],
    ):
        self._sources = sources
        self._targets = targets
        if func := self.parent_func:
            for op in operations:
                op._func = func
        self._operations = operations
        self._mark_dirty()

    @staticmethod
    def from_encoding(region: schema.Region, parent: FunctionDef | JeffOp):
        obj = JeffRegion.__new__(JeffRegion)
        obj._raw_data = region
        obj._parent = parent
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self) -> bool:
        """Whether the object has been modified since the last time it was encoded. Also returns
        True if the object has never been written out (e.g. after instantiation)."""
        return self._is_dirty

    def _mark_clean(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = False

    def _mark_dirty(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = True
        if self._parent:
            self._parent._mark_dirty()

    def _refresh(self, new_data: schema.Region.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """

        _sources = self.sources
        sources = new_data.init("sources", len(_sources))
        for i, val in enumerate(_sources):
            sources[i] = val._val_idx  # no need to search the value table

        _targets = self.targets
        targets = new_data.init("targets", len(_targets))
        for i, val in enumerate(_targets):
            targets[i] = val._val_idx

        _operations = self.operations
        operations = new_data.init("operations", len(_operations))
        for i, op in enumerate(_operations):
            op._refresh(operations[i], string_table)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._sources = self.sources
        self._targets = self.targets
        self._operations = self.operations
        for op in self._operations:
            op._update_cache()

    # settable fields

    @property
    def sources(self) -> list[JeffValue]:
        if self._sources is not _Empty:
            return self._sources

        return [
            JeffValue.from_encoding(source, self.parent_func)
            for source in self._raw_data.sources
        ]

    @sources.setter
    def sources(self, sources: list[JeffValue]):
        self._sources = sources
        self._mark_dirty()

    @property
    def targets(self) -> list[JeffValue]:
        if self._targets is not _Empty:
            return self._targets

        return [
            JeffValue.from_encoding(target, self.parent_func)
            for target in self._raw_data.targets
        ]

    @targets.setter
    def targets(self, targets: list[JeffValue]):
        # no need
        self._targets = targets
        self._mark_dirty()

    @property
    def operations(self) -> list[JeffOp]:
        if self._operations is not _Empty:
            return self._operations

        return [
            JeffOp.from_encoding(op, self.parent_func)
            for op in self._raw_data.operations
        ]

    @operations.setter
    def operations(self, operations: list[JeffOp]):
        if func := self.parent_func:
            for op in operations:
                op._func = func
        self._operations = operations
        self._mark_dirty()

    # convenience methods

    @property
    def parent_func(self) -> FunctionDef | None:
        if isinstance(self._parent, FunctionDef):
            return self._parent
        elif isinstance(self._parent, JeffSCF):
            return getattr(self._parent._op, "_func", None)

        return None

    # Python integration

    def __getitem__(self, idx):
        if self._operations is not _Empty:
            return self._operations[idx]

        return JeffOp.from_encoding(self._raw_data.operations[idx], self.parent_func)

    def __str__(self):
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


class JeffFunc(ABC):
    """Jeff supports both function definitions (with a body) and declarations (with a signature).
    For both the name is stored as a string attribute."""

    _is_dirty: bool
    _raw_data: schema.Function = None
    _module: JeffModule = None

    # cached attributes
    _name: str = _Empty

    @staticmethod
    def from_encoding(func: schema.Function, module: JeffModule):
        """Construct a function from encoded data. This provides a zero-copy view of the data."""
        cls = {"definition": FunctionDef, "declaration": FunctionDecl}[str(func.which)]
        obj = cls.__new__(cls)
        obj._raw_data = func
        obj._module = module
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self) -> bool:
        """Whether the object has been modified since the last time it was encoded. Also returns
        True if the object has never been written out (e.g. after instantiation)."""
        return self._is_dirty

    def _mark_clean(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = False

    def _mark_dirty(self):
        """An object can be marked clean by itself, but a dirty tag is always propagated upward."""
        self._is_dirty = True
        if self._module:
            self._module._mark_dirty()

    # settable fields

    @property
    def name(self) -> str:
        if self._name is not _Empty:
            return self._name

        assert not self._module.is_dirty, (
            "The parent module is dirty and no name has been cached. "
            "Please call `refresh` on the module to access this attribute."
        )

        idx = self._raw_data.name
        return self._module.string_table[idx]

    @name.setter
    def name(self, name: str):
        self._name = name
        self._mark_dirty()

    # convenience methods

    @property
    @abstractmethod
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        """Return the input/output type signature of the function."""

    # Python integration

    def __str__(self):
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


class FunctionDef(JeffFunc):
    """Function definitions contain a single region determining the call signature of the function.
    The encoded object also contains a value table for all typed values in the program."""

    # cached attributes
    _body: JeffRegion = _Empty

    def __init__(self, name: str, body: JeffRegion):
        self._name = name
        body._parent = self
        self._body = body
        self._mark_dirty()

    def _refresh(self, new_data: schema.Function.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        definition = new_data.init("definition")

        _values = self._compute_values()
        values = definition.init("values", len(_values))
        for i, val in enumerate(_values):
            val._refresh(values[i])
            # updating the value index here means we don't need to pass the value table
            # down to operations etc, since the index is stored in the value itself
            val._val_idx = i

        self.body._refresh(definition.body, string_table)

        # strings are stored as indices in the encoded format
        new_data.name = string_table.index(self.name)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._name = self.name
        self._body = self.body
        self.body._update_cache()

    # settable fields

    @property
    def body(self) -> JeffRegion:
        if self._body is not _Empty:
            return self._body

        return JeffRegion.from_encoding(self._raw_data.definition.body, self)

    @body.setter
    def body(self, body: JeffRegion):
        for op in body.operations:
            op._func = self
        body._parent = self
        self._body = body
        self._mark_dirty()

    # encoding-only fields

    @property
    def value_table(self) -> Iterable[schema.Value]:
        assert not self.is_dirty, (
            "The FunctionDef contains some cached data, but the value table is only accessible "
            "from the encoded format. Please call `refresh` before accessing this attribute."
        )

        return self._raw_data.definition.values

    def _compute_values(self) -> list[JeffValue]:
        """Get a fresh value table from the cached program. Requires whole-function traversal."""
        values = []
        regions = [self.body]

        while regions:
            current_region = regions.pop(0)

            for val in current_region.sources:
                values.append(val)

            for op in current_region:
                for val in op.outputs:
                    values.append(val)

                data = op.instruction_data
                if isinstance(data, SwitchSCF):
                    for branch in data.branches:
                        regions.append(branch)
                    if data.default:
                        regions.append(data.default)
                elif isinstance(data, ForSCF):
                    regions.append(data.body)
                elif isinstance(data, (WhileSCF, DoWhileSCF)):
                    regions.append(data.condition)
                    regions.append(data.body)

        return values

    # convenience methods

    @property
    def sources(self) -> list[JeffValue]:
        return self.body.sources

    @property
    def targets(self) -> list[JeffValue]:
        return self.body.targets

    @property
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        input_types = [inp.type for inp in self.sources]
        output_types = [out.type for out in self.targets]
        return input_types, output_types

    # Python integration

    def __getitem__(self, idx):
        if self._body is not _Empty:
            return self._body[idx]

        return JeffOp.from_encoding(
            self._raw_data.definition.body.operations[idx], self
        )


class FunctionDecl(JeffFunc):
    """Function declarations contain only the input/output type signature."""

    # cached attributes
    _inputs: list[JeffType] = _Empty
    _outputs: list[JeffType] = _Empty

    def __init__(self, name: str, inputs: list[JeffType], outputs: list[JeffType]):
        self._name = name
        self._inputs = inputs
        self._outputs = outputs
        self._mark_dirty()

    def _refresh(self, new_data: schema.Function.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        declaration = new_data.init("declaration")

        _inputs = self.inputs
        inputs = declaration.init("inputs", len(_inputs))
        for i, input in enumerate(_inputs):
            input._refresh(inputs[i])

        _outputs = self.outputs
        outputs = declaration.init("outputs", len(_outputs))
        for i, output in enumerate(_outputs):
            output._refresh(outputs[i])

        # strings are stored as indices in the encoded format
        new_data.name = string_table.index(self.name)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._name = self.name
        self._inputs = self.inputs
        self._outputs = self.outputs

    # settable fields

    @property
    def inputs(self) -> list[JeffType]:
        if self._inputs is not _Empty:
            return self._inputs

        return [
            JeffType.from_encoding(inp.type)
            for inp in self._raw_data.declaration.inputs
        ]

    @inputs.setter
    def inputs(self, inputs: list[JeffType]):
        self._inputs = inputs
        self._mark_dirty()

    @property
    def outputs(self) -> list[JeffType]:
        if self._outputs is not _Empty:
            return self._outputs

        return [
            JeffType.from_encoding(out.type)
            for out in self._raw_data.declaration.outputs
        ]

    @outputs.setter
    def outputs(self, outputs: list[JeffType]):
        self._outputs = outputs
        self._mark_dirty()

    # convenience methods

    @property
    def function_type(self) -> tuple[list[JeffType], list[JeffType]]:
        return self.inputs, self.outputs


class JeffModule:
    """The module is the root node in the program. It's a container for functions,
    as well as certain metadata. The encoded object also stores a string table for all string
    attributes in the program."""

    _is_dirty: bool
    _raw_data: schema.Module = None

    # cached attributes
    _functions: list[JeffFunc] = _Empty
    _entrypoint: int = _Empty
    _version: int = _Empty
    _tool: str = _Empty
    _tool_version: str = _Empty

    def __init__(
        self,
        functions: list[JeffFunc],
        entrypoint: int = 0,
        version: int = 0,
        tool: str = "",
        tool_version: str = "",
    ):
        """Build a JeffModule from its children fields. The data is cached until `write-out`
        is called, upon which the data is encoded in the jeff binary format."""
        for func in functions:
            func._module = self
        self._functions = functions
        self._entrypoint = entrypoint
        self._version = version
        self._tool = tool
        self._tool_version = tool_version
        self._mark_dirty()

    @staticmethod
    def from_encoding(module: schema.Module):
        """Construct a JeffModule from encoded data. This provides a zero-copy view of the data."""
        obj = JeffModule.__new__(JeffModule)
        obj._raw_data = module
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self) -> bool:
        """Whether the object has been modified since the last time it was encoded. Also returns
        True if the object has never been written out (e.g. after instantiation)."""
        return self._is_dirty

    def _mark_clean(self):
        self._is_dirty = False

    def _mark_dirty(self):
        self._is_dirty = True

    def refresh(self):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        if not self.is_dirty:
            return

        # Reusing an existing message is a bad idea as any new allocations will leave the old ones
        # in the message, bloating its size.
        new_data = schema.Module.new_message()

        _strings = self._compute_strings()
        strings = new_data.init("strings", len(_strings))
        for i, string in enumerate(_strings):
            strings[i] = string

        functions = new_data.init("functions", len(self._functions))
        for i, func in enumerate(self._functions):
            func._refresh(functions[i], _strings)

        new_data.entrypoint = self.entrypoint
        new_data.version = self.version
        new_data.tool = self.tool
        new_data.toolVersion = self.tool_version

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def write_out(self, path: str = None):
        """Write out the program to file. Only available on the module object as the root node.
        Automatically calls `refresh` before writing.
        """
        self.refresh()

        with open(path, "wb") as f:
            self._raw_data.write(f)

    # settable fields

    @property
    def functions(self) -> list[JeffFunc]:
        """For read-only access, iterate over / index into the module directly."""
        if self._functions is not _Empty:
            return self._functions

        return [JeffFunc.from_encoding(func, self) for func in self._raw_data.functions]

    @functions.setter
    def functions(self, functions: list[JeffFunc]):
        for func in functions:
            # "adopting" a read-only object will detach it from its original encoded message,
            # so let's load any data associated to it into cache
            func._update_cache()
            func._module = self
        self._functions = functions
        self._mark_dirty()

    # encoding-only fields

    @property
    def string_table(self) -> Iterable[str]:
        assert not self.is_dirty, (
            "The JeffModule contains some cached data, but the string table is only accessible "
            "from the encoded format. Please call `refresh` or `write_out` before accessing this "
            "attribute."
        )
        return self._raw_data.strings

    def _compute_strings(self) -> list[str]:
        """Get a fresh string table from the cached program. Requires whole-program traversal."""
        strings = set()
        regions = []

        for func in self._functions:
            strings.add(func.name)
            regions.append(func.body)

        while regions:
            current_region = regions.pop(0)

            for op in current_region:
                data = op.instruction_data
                if isinstance(data, CustomGate):
                    strings.add(data.name)

                if isinstance(data, SwitchSCF):
                    for branch in data.branches:
                        regions.append(branch)
                    if data.default:
                        regions.append(data.default)
                elif isinstance(data, ForSCF):
                    regions.append(data.body)
                elif isinstance(data, (WhileSCF, DoWhileSCF)):
                    regions.append(data.condition)
                    regions.append(data.body)

        return list(strings)

    # static fields

    @property
    def entrypoint(self) -> int:
        if self._entrypoint is not _Empty:
            return self._entrypoint

        return self._raw_data.entrypoint

    @property
    def version(self) -> int:
        if self._version is not _Empty:
            return self._version

        return self._raw_data.version

    @property
    def tool(self) -> str:
        if self._version is not _Empty:
            return self._tool

        return self._raw_data.tool

    @property
    def tool_version(self) -> str:
        if self._tool_version is not _Empty:
            return self._tool_version

        return self._raw_data.toolVersion

    # Python integration

    def __getitem__(self, idx):
        if self._functions is not _Empty:
            return self._functions[idx]

        return JeffFunc.from_encoding(self._raw_data.functions[idx], self)

    def __str__(self):
        string = f"jeff v{self.version}"

        if self.tool:
            string += f", {self.tool} v{self.tool_version}"
        string += "\n\n"

        for i, func in enumerate(self):
            string += f"{'[entry] ' if i == self.entrypoint else ''}{func}\n"

        return string


################
# Instructions #
################


class JeffGate(ABC):
    """Instruction data for quantum gate operations."""

    _is_dirty: bool
    _raw_data: schema.QubitGate = None
    _op: JeffOp = None

    # common cached fields
    _num_controls: int = _Empty
    _adjoint: bool = _Empty
    _power: int = _Empty

    def from_encoding(gate: schema.QubitGate, op: JeffOp):
        cls = {"custom": CustomGate, "wellKnown": WellKnowGate, "ppr": PPRGate}[
            str(gate.which)
        ]
        obj = cls.__new__(cls)
        obj._raw_data = gate
        obj._op = op
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self):
        return self._is_dirty

    def _mark_clean(self):
        self._is_dirty = False

    def _mark_dirty(self):
        self._is_dirty = True
        if self._op:
            self._op._mark_dirty()

    def _refresh(self, new_data: schema.QubitGate.Builder):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """

        new_data.controlQubits = self.num_controls
        new_data.adjoint = self.adjoint
        new_data.power = self.power

    # settable fields

    @property
    def num_controls(self) -> int:
        if self._num_controls is not _Empty:
            return self._num_controls

        return self._raw_data.controlQubits

    @num_controls.setter
    def num_controls(self, num_controls: int):
        self._num_controls = num_controls
        self._mark_dirty()

    @property
    def adjoint(self) -> bool:
        if self._adjoint is not _Empty:
            return self._adjoint

        return self._raw_data.adjoint

    @adjoint.setter
    def adjoint(self, adjoint: int):
        self._adjoint = adjoint
        self._mark_dirty()

    @property
    def power(self) -> int:
        if self._power is not _Empty:
            return self._power

        return self._raw_data.power

    @power.setter
    def power(self, power: int):
        self._power = power
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = ""
        if num_controls := self.num_controls:
            string += f"numControls={num_controls}, "
        if self.adjoint:
            string += "adjoint, "
        if (power := self.power) != 1:
            string += f"power={power}, "
        return string


class WellKnowGate(JeffGate):
    """Specialization of gate intruction data for well-known gates. Well-known gates must be one of
    the gates defined in the spec. No additional data needs to be specified."""

    _kind: str = _Empty

    def __init__(self, kind: str, num_controls: int, adjoint: bool, power: int):
        assert kind in KnownGates
        self._kind = kind
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _refresh(self, new_data: schema.QubitGate.Builder, _string_table):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """

        new_data.wellKnown = self.kind
        super()._refresh(new_data)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def kind(self):
        if self._kind is not _Empty:
            return self._kind

        return str(self._raw_data.wellKnown.which)

    @kind.setter
    def kind(self, kind: str):
        assert kind in KnownGates
        self._kind = kind
        self._mark_dirty()

    # convenience methods

    @property
    def num_qubits(self):
        match self.kind:
            case "gphase":
                return 0
            case (
                "i"
                | "x"
                | "y"
                | "z"
                | "s"
                | "t"
                | "r1"
                | "rx"
                | "ry"
                | "rz"
                | "h"
                | "u"
            ):
                return 1
            case "swap":
                return 2

        assert False, "unknown gate"

    @property
    def num_params(self):
        match self.kind:
            case "i" | "x" | "y" | "z" | "s" | "t" | "h":
                return 0
            case "gphase" | "r1" | "rx" | "ry" | "rz":
                return 1
            case "u":
                return 3

        assert False, "unknown gate"

    # Python integration

    def __str__(self):
        string = f"({self.kind}, "
        string += super().__str__()
        string = string[:-2] + ")"
        return string


class CustomGate(JeffGate):
    """Specialization of gate intruction data for custom gates. Custom gates are identified by a
    string name, and also have to provide the number of qubits and number float parameters."""

    _name: str = _Empty
    _num_qubits: int = _Empty
    _num_params: int = _Empty

    def __init__(
        self,
        name: str,
        num_qubits: int,
        num_params: int,
        num_controls: int,
        adjoint: bool,
        power: int,
    ):
        self._name = name
        self._num_qubits = num_qubits
        self._num_params = num_params
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _refresh(self, new_data: schema.QubitGate.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        custom = new_data.init("custom")

        custom.name = string_table.index(self.name)
        custom.numQubits = self.num_qubits
        custom.numParams = self.num_params
        super()._refresh(new_data)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._name = self.name

    # settable fields

    @property
    def name(self) -> str:
        if self._name is not _Empty:
            return self._name

        assert (
            (func := self._op._func) and (mod := func._module) and not mod.is_dirty
        ), (
            "The parent module is not present or dirty, and no name has been cached. "
            "Please call `refresh` on the module to access this attribute."
        )

        return self._op._func._module.string_table[self._raw_data.custom.name]

    @name.setter
    def name(self, name: str):
        self._name = name
        self._mark_dirty()

    @property
    def num_qubits(self) -> int:
        if self._num_qubits is not _Empty:
            return self._num_qubits

        return self._raw_data.custom.numQubits

    @num_qubits.setter
    def num_qubits(self, num_qubits: int):
        self._num_qubits = num_qubits
        self._mark_dirty()

    @property
    def num_params(self) -> int:
        if self._num_params is not _Empty:
            return self._num_params

        return self._raw_data.custom.numParams

    @num_params.setter
    def num_params(self, num_params: int):
        self._num_params = num_params
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = f'("{self.name}", '
        string += f"numQubits={self.num_qubits}, "
        if numParams := self.num_params:
            string += f"numParams={numParams}, "
        string += super().__str__()
        string = string[:-2] + ")"
        return string


class PPRGate(JeffGate):
    """Specialization of gate intruction data for pauli-product rotation gates. Custom gates are
    identified by a string name, and also have to provide the number of qubits and number float
    parameters."""

    _pauli_string: list[str] = _Empty

    def __init__(
        self, pauli_string: list[str], num_controls: int, adjoint: bool, power: int
    ):
        self._pauli_string = pauli_string
        self._num_controls = num_controls
        self._adjoint = adjoint
        self._power = power
        self._mark_dirty()

    def _refresh(self, new_data: schema.QubitGate.Builder, _string_table):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        ppr = new_data.init("ppr")

        _pauli_string = self.pauli_string
        pauli_string = ppr.init("pauliString", len(_pauli_string))
        for i, pauli in enumerate(_pauli_string):
            pauli_string[i] = pauli
        super()._refresh(new_data)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    # settable fields

    @property
    def pauli_string(self) -> list[str]:
        if self._pauli_string is not _Empty:
            return self._pauli_string

        return [str(pauli) for pauli in self._raw_data.ppr.pauliString]

    @pauli_string.setter
    def pauli_string(self, pauli_string: list[str]):
        assert all(pauli in Paulis for pauli in pauli_string)
        self._pauli_string = pauli_string
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = "(PPR, "
        string += f"pauliString={self.pauli_string}, "
        string += super().__str__()
        string = string[:-2] + ")"
        return string


class JeffSCF(ABC):
    """Instruction data for a structured control-flow (SCF) operations."""

    _is_dirty: bool
    _raw_data: schema.ScfOp = None
    _op: JeffOp = None

    def from_encoding(scf: schema.ScfOp, op: JeffOp):
        cls = {
            "switch": SwitchSCF,
            "for": ForSCF,
            "while": WhileSCF,
            "doWhile": DoWhileSCF,
        }[str(scf.which)]
        obj = cls.__new__(cls)
        obj._raw_data = scf
        obj._op = op
        obj._mark_clean()
        return obj

    @property
    def is_dirty(self):
        return self._is_dirty

    def _mark_clean(self):
        self._is_dirty = False

    def _mark_dirty(self):
        self._is_dirty = True
        if self._op:
            self._op._mark_dirty()


class SwitchSCF(JeffSCF):
    """Switch-statement specialization of the JeffSCF instruction data class.
    Switch operations contain a list of regions that are indexed into by an integer parameter,
    as well as an optional default region that is triggered when the index is out of bounds.
    All regions must have the same input/output port signature."""

    _branches: list[JeffRegion] = _Empty
    _default: JeffRegion = _Empty

    def __init__(self, branches: list[JeffRegion], default: JeffRegion = None):
        for branch in branches:
            branch._parent = self
        self._branches = branches
        if default:
            default._parent = self
        self._default = default
        self._mark_dirty()

    def _refresh(self, new_data: schema.ScfOp.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        switch = new_data.init("switch")

        _branches = self.branches
        branches = switch.init("branches", len(_branches))
        for i, branch in enumerate(_branches):
            branch._refresh(branches[i], string_table)

        if _default := self.default:
            _default._refresh(switch.default, string_table)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._branches = self.branches
        self._default = self.default
        for branch in self.branches:
            branch._update_cache()
        if default := self.default:
            default._update_cache()

    # settable fields

    @property
    def branches(self) -> list[JeffRegion]:
        if self._branches is not _Empty:
            return self._branches

        return [
            JeffRegion.from_encoding(branch, self)
            for branch in self._raw_data.switch.branches
        ]

    @branches.setter
    def branches(self, branches: list[JeffRegion]):
        for branch in branches:
            branch._update_cache()
            branch._parent = self
        self._branches = branches
        self._mark_dirty()

    @property
    def default(self) -> JeffRegion | None:
        if self._default is not _Empty:
            return self._default

        if region := self._raw_data.switch.default:
            return JeffRegion.from_encoding(region, self)

    @default.setter
    def default(self, default: JeffRegion):
        default._update_cache()
        default._parent = self
        self._default = default
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = "\n"

        for i, branch in enumerate(self.branches):
            string += f"  case {i}:\n"
            string += f"{textwrap.indent(str(branch), '  ')}"

        if branch := self.default:
            string += "\n"
            string += "  default:\n"
            string += f"{textwrap.indent(str(branch), '  ')}"

        return string


class ForSCF(JeffSCF):
    """For-loop specialization of the JeffSCF instruction data class.
    For loop operations contain a single region that represents the loop body.
    The loop iterates from start to stop (exclusive) by step, maintaining state from region output
    to input ports."""

    _body: JeffRegion = _Empty

    def __init__(self, body: JeffRegion):
        body._parent = self
        self._body = body
        self._mark_dirty()

    def _refresh(self, new_data: schema.ScfOp.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        # the 'for' member is not its own struct, instead it directly stores the body region
        forloop = new_data.init("for")

        _body = self.body
        _body._refresh(forloop, string_table)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""
        self._body = self.body
        self._body._update_cache()

    # settable fields

    @property
    def body(self) -> JeffRegion:
        if self._body is not _Empty:
            return self._body

        return JeffRegion.from_encoding(getattr(self._raw_data, "for"), self)

    @body.setter
    def body(self, body: JeffRegion):
        body._update_cache()
        body._parent = self
        self._body = body
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = "\n"
        string += "  body:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        return string


class WhileSCF(JeffSCF):
    """While-loop specialization of the JeffSCF instruction data class.
    While loop operations contain two regions: a condition region and a body region.
    The condition region is executed before each iteration and accepts the state as input, but
    only produces a bool as output. The body region takes the same state as input and output."""

    _condition: JeffRegion = _Empty
    _body: JeffRegion = _Empty

    def __init__(self, condition: JeffRegion, body: JeffRegion):
        condition._parent = self
        self._condition = condition
        body._parent = self
        self._body = body
        self._mark_dirty()

    def _refresh(self, new_data: schema.ScfOp.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        whileloop = new_data.init("while")

        _condition = self.condition
        _condition._refresh(whileloop.condition, string_table)

        _body = self.body
        _body._refresh(whileloop.body, string_table)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""

        self._condition = self.condition
        self._body = self.body
        self._condition._update_cache()
        self._body._update_cache()

    # settable fields

    @property
    def condition(self) -> JeffRegion:
        if self._condition is not _Empty:
            return self._condition

        return JeffRegion.from_encoding(
            getattr(self._raw_data, "while").condition, self
        )

    @condition.setter
    def condition(self, condition: JeffRegion):
        condition._update_cache()
        condition._parent = self
        self._condition = condition
        self._mark_dirty()

    @property
    def body(self) -> JeffRegion:
        if self._body is not _Empty:
            return self._body

        return JeffRegion.from_encoding(getattr(self._raw_data, "while").body, self)

    @body.setter
    def body(self, body: JeffRegion):
        body._update_cache()
        body._parent = self
        self._body = body
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = "\n"
        string += "  while:\n"
        string += f"{textwrap.indent(str(self.condition), '  ')}"
        string += "  do:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        return string


class DoWhileSCF(JeffSCF):
    """Do-while-loop specialization of the JeffSCF instruction data class.
    Do-while loop operations contain two regions: a body region and a condition region.
    The body is executed first, then the condition is checked. The region sigantures are the same
    as for the while loop."""

    _body: JeffRegion = _Empty
    _condition: JeffRegion = _Empty

    def __init__(self, body: JeffRegion, condition: JeffRegion):
        body._parent = self
        self._body = body
        condition._parent = self
        self._condition = condition
        self._mark_dirty()

    def _refresh(self, new_data: schema.ScfOp.Builder, string_table: list[str]):
        """Refresh this object's encoded data with cached modifications. Also refreshes all child
        objects. This method guarantees that `is_dirty` is False after invocation.
        When is `is_dirty` is already False, this method does nothing.
        """
        doWhile = new_data.init("doWhile")

        self.body._refresh(doWhile.body, string_table)
        self.condition._refresh(doWhile.condition, string_table)

        self._raw_data = new_data.as_reader()
        self._mark_clean()

    def _update_cache(self):
        """TESTING ONLY. Update the cached attributes of this object. This effectively transitions
        the object from "reader" mode to "writer" mode, e.g. as part of building a new module."""

        self._body = self.body
        self._condition = self.condition
        self._body._update_cache()
        self._condition._update_cache()

    # settable fields

    @property
    def body(self) -> JeffRegion:
        if self._body is not _Empty:
            return self._body

        return JeffRegion.from_encoding(self._raw_data.doWhile.body, self)

    @body.setter
    def body(self, body: JeffRegion):
        body._update_cache()
        body._parent = self
        self._body = body
        self._mark_dirty()

    @property
    def condition(self) -> JeffRegion:
        if self._condition is not _Empty:
            return self._condition

        return JeffRegion.from_encoding(self._raw_data.doWhile.condition, self)

    @condition.setter
    def condition(self, condition: JeffRegion):
        condition._update_cache()
        condition._parent = self
        self._condition = condition
        self._mark_dirty()

    # Python integration

    def __str__(self):
        string = "\n"
        string += "  do:\n"
        string += f"{textwrap.indent(str(self.body), '  ')}"
        string += "  while:\n"
        string += f"{textwrap.indent(str(self.condition), '  ')}"
        return string


#################
# API functions #
#################

# reading


def load_module(path: str):
    """Load a jeff module from file."""

    with open(path, "rb") as f:
        return JeffModule.from_encoding(schema.Module.read(f))


# building


def qubit_alloc():
    """Single qubit alloc operation."""
    inputs = []
    outputs = [JeffValue(QubitType())]
    return JeffOp("qubit", "alloc", inputs, outputs)


def qubit_free(qubit: JeffValue):
    """Single qubit free operation."""
    inputs = [qubit]
    outputs = []
    return JeffOp("qubit", "free", inputs, outputs)


def quantum_gate(
    name: str,
    qubits: JeffValue | list[JeffValue],
    params: list[float] = None,
    control_qubits: list[JeffValue] = None,
    adjoint: bool = False,
    power: int = 1,
):
    """Instantiate a well-known or custom gate operation."""
    qubits = [qubits] if isinstance(qubits, JeffValue) else qubits
    params = params or []
    control_qubits = control_qubits or []

    if name in KnownGates:
        gate = WellKnowGate(name, len(control_qubits), adjoint, power)
    else:
        gate = CustomGate(
            name, len(qubits), len(params), len(control_qubits), adjoint, power
        )
    qubit_inputs = qubits + control_qubits
    inputs = qubit_inputs + params
    outputs = [JeffValue(QubitType()) for _ in qubit_inputs]
    return JeffOp("qubit", "gate", inputs, outputs, instruction_data=gate)


def pauli_rotation(
    angle: JeffValue,
    pauli_string: str | list[str],
    qubits: JeffValue | list[JeffValue],
    control_qubits: list[JeffValue] = None,
    adjoint: bool = False,
    power: int = 1,
):
    """Instantiate a Pauli-product rotation operation."""
    pauli_string = [pauli_string] if isinstance(pauli_string, str) else pauli_string
    qubits = [qubits] if isinstance(qubits, JeffValue) else qubits
    control_qubits = control_qubits or []
    assert len(pauli_string) == len(qubits)

    ppr = PPRGate(pauli_string, len(control_qubits), adjoint, power)
    inputs = qubits + control_qubits + [angle]
    outputs = [JeffValue(QubitType()) for _ in inputs[:-1]]
    return JeffOp("qubit", "gate", inputs, outputs, instruction_data=ppr)


def bitwise_not(x: JeffValue):
    """Instantiate a bitwise NOT operation."""
    inputs = [x]
    outputs = [JeffValue(x.type)]
    return JeffOp("int", "not", inputs, outputs)


def switch_case(
    index: JeffValue,
    region_args: list[JeffValue],
    branches: list[JeffRegion],
    default: JeffRegion = None,
):
    """Instantiate a switch-case operation. Cases run from 0 to len(branches)-1."""
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
    outputs = [JeffValue(val.type) for val in branches[0].targets]

    return JeffOp("scf", "switch", inputs, outputs, instruction_data=scf)
