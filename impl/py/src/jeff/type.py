"""Jeff type definitions."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from .capnp import schema, CapnpBuffer
from .string_table import StringTable


class FloatPrecision(Enum):
    FLOAT32 = "float32"
    FLOAT64 = "float64"

    @staticmethod
    def from_name(name: str) -> FloatPrecision:
        match name.lower():
            case "float32":
                return FloatPrecision.FLOAT32
            case "float64":
                return FloatPrecision.FLOAT64
        raise ValueError(f"Unknown float precision: {name}")


class JeffType(ABC, CapnpBuffer[schema.Type, schema.Type.Builder]):  # type: ignore
    """A Jeff type."""

    @staticmethod
    def _read_from_buffer(reader: schema.Type):  # type: ignore
        match reader.which:
            case "qubit":
                return QubitType()
            case "qureg":
                return QuregType()
            case "int":
                bitwidth = reader.int
                return IntType(bitwidth)
            case "intArray":
                bitwidth = reader.intArray
                return IntArrayType(bitwidth)
            case "float":
                float_width = FloatPrecision.from_name(reader.float)
                return FloatType(float_width)
            case "floatArray":
                float_width = FloatPrecision.from_name(reader.floatArray)
                return FloatArrayType(float_width)
            case _:
                raise ValueError(f"Unknown type: {reader.which}")

    def _force_read_all(self) -> None:
        pass


@dataclass(frozen=True)
class QubitType(JeffType):
    """A qubit type."""

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        new_data.qubit = None

    def __str__(self) -> str:
        return "qubit"


@dataclass(frozen=True)
class QuregType(JeffType):
    """A register of qubits with arbitrary size."""

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        new_data.qureg = None

    def __str__(self) -> str:
        return "qureg"


@dataclass(frozen=True)
class IntType(JeffType):
    """An integer type, with a fixed bitwidth."""

    bitwidth: int

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        new_data.int = self.bitwidth

    def __str__(self) -> str:
        return f"int{self.bitwidth}"


@dataclass(frozen=True)
class IntArrayType(JeffType):
    """Specialization of the JeffType for integer arrays."""

    bitwidth: int

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore[name-defined]
        string_table: StringTable,
    ) -> None:
        new_data.intArray = self.bitwidth

    def __str__(self) -> str:
        return f"int{self.bitwidth}[]"


@dataclass(frozen=True)
class FloatType(JeffType):
    """Specialization of the JeffType for floating point values."""

    bitwidth: FloatPrecision

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        new_data.float = self.bitwidth.value

    def __str__(self) -> str:
        return f"{self.bitwidth.value}"


@dataclass(frozen=True)
class FloatArrayType(JeffType):
    """Specialization of the JeffType for floating point arrays."""

    bitwidth: FloatPrecision

    def _write_to_buffer(
        self,
        new_data: schema.Type.Builder,  # type: ignore
        string_table: StringTable,
    ) -> None:
        new_data.floatArray = self.bitwidth

    def __str__(self) -> str:
        return f"{self.bitwidth.value}[]"
