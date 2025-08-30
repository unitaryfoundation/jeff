"""Jeff operation definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing_extensions import override

from jeff.capnp import CapnpBuffer, LazyUpdate, schema
from jeff.op.kind import OpKind, OpType
from jeff.op.qubit import QubitGate
from jeff.op.qubit.non_unitary import NonUnitaryOp
from jeff.op.scf import Scf
from jeff.string_table import StringTable
from jeff.value import Value


if TYPE_CHECKING:
    from jeff.region import Region
    from jeff.function import FunctionDef


class JeffOp(CapnpBuffer[schema.Op, schema.Op.Builder], LazyUpdate):  # type: ignore
    """A generic container for all operations in the program.

    The common fields include input and output values, as well as the kind of
    operation represented. All ops have a main kind (like QubitOp and IntOp), as
    well as a subkind (like alloc, add, etc.). Some operations store additional
    data as well, which can be primitive types as well extra classes defined in
    the API.
    """

    # The read-only buffer backing this object.
    _raw_data: schema.Op | None = None  # type: ignore

    # Reference to the containing function.
    _func: FunctionDef | None = None
    # Reference to the containing region.
    _region: Region | None = None

    # Input values to the operation
    _inputs: list[Value] | None = None
    # Output values from the operation
    _outputs: list[Value] | None = None
    # The operation type
    _op_type: OpType[Any, Any]

    def __init__(
        self,
        op_type: OpType[Any, Any],
        inputs: list[Value],
        outputs: list[Value],
    ):
        op_type._op = self
        self._inputs = inputs
        self._outputs = outputs
        self._op_type = op_type
        self._mark_dirty()

    @override
    def _mark_dirty(self) -> None:
        """Mark the object as dirty.

        This call spreads recursively to parent objects.
        """
        self._is_dirty = True
        if self._func:
            self._func._mark_dirty()

    @staticmethod
    def _read_from_buffer(op: schema.Op) -> JeffOp:  # type: ignore
        obj = JeffOp.__new__(JeffOp)
        obj._raw_data = op

        match op.instruction.which:
            case "qubit":
                qubit = op.instruction.qubit
                match qubit.which:
                    case "gate":
                        obj._op_type = QubitGate._read_from_buffer(qubit.gate)
                    case _:
                        obj._op_type = NonUnitaryOp._read_from_buffer(qubit)
            case "scf":
                obj._op_type = Scf._read_from_buffer(op.instruction.scf)
            case _:
                raise ValueError(f"unknown operation type: {op.instruction.which}")
        obj._op_type._op = obj
        obj._mark_clean()
        return obj

    def _force_read_all(self) -> None:
        _ = self.inputs
        _ = self.outputs
        self._op_type._force_read_all()
        self._mark_dirty()

    def _write_to_buffer(
        self,
        writer: schema.Op.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        """Write any cached modifications back to the capnp buffer."""

        _inputs = self.inputs
        inputs = writer.init("inputs", len(_inputs))
        for i, val in enumerate(_inputs):
            inputs[i] = val.id  # no need to search the value table

        _outputs = self.outputs
        outputs = writer.init("outputs", len(_outputs))
        for i, val in enumerate(_outputs):
            outputs[i] = val.id

        instruction_group = writer.instruction.init(self.op_type.op_kind.kind)
        match self.op_type.op_kind:
            case OpKind.QUBIT_GATE:
                gate = instruction_group.init("gate")
                self.op_type._write_to_buffer(gate, string_table)
            case OpKind.SCF:
                self.op_type._write_to_buffer(instruction_group, string_table)
            case _:
                raise ValueError(f"unknown operation type: {self.op_type.op_kind}")

        self._raw_data = writer.as_reader()
        self._mark_clean()

    # cached fields

    @property
    def inputs(self) -> list[Value]:
        """The input values to the operation."""
        if self._inputs is None:
            if self._func is None:
                raise ValueError(
                    "Input values haven't been assigned yet to operation without parent function"
                )
            if self._raw_data is None:
                raise ValueError("Input values haven't been assigned yet")
            self._inputs = []
            for input_id in self._raw_data.inputs:
                val = self._func.value_table[input_id]
                self._inputs.append(val)
        return self._inputs

    @inputs.setter
    def inputs(self, inputs: list[Value]) -> None:
        if self._func is not None:
            for val in inputs:
                self._func.value_table.add(val)
        self._inputs = inputs
        self._mark_dirty()

    @property
    def outputs(self) -> list[Value]:
        if self._outputs is None:
            if self._func is None:
                raise ValueError(
                    "Output values haven't been assigned yet to operation without parent function"
                )
            if self._raw_data is None:
                raise ValueError("Output values haven't been assigned yet")
            self._outputs = []
            for output_id in self._raw_data.outputs:
                val = self._func.value_table[output_id]
                self._outputs.append(val)
        return self._outputs

    @outputs.setter
    def outputs(self, outputs: list[Value]) -> None:
        if self._func is not None:
            for val in outputs:
                self._func.value_table.add(val)
        self._outputs = outputs
        self._mark_dirty()

    @property
    def op_type(self) -> OpType[Any, Any]:
        return self._op_type

    @op_type.setter
    def op_type(self, op_type: OpType[Any, Any]) -> None:
        op_type._op = self
        self._op_type = op_type
        self._mark_dirty()

    # static fields

    @property
    def kind(self) -> OpKind:
        return self.op_type.op_kind

    # convenience methods

    def get_value(self, idx: int) -> Value:
        """Returns a value from the function's value table."""
        if self._func is None:
            raise ValueError(
                "Value haven't been assigned yet to operation without parent function"
            )
        return self._func.value_table[idx]

    # Python integrations

    def __str__(self) -> str:
        string = ""

        if outputs := self.outputs:
            string += ", ".join(str(out) for out in outputs)
            string += " = "

        string += f"{self.kind} "

        string += ", ".join(str(inp) for inp in self.inputs)

        if (data := self.kind) is not None:
            string += f" {data}"

        return string
