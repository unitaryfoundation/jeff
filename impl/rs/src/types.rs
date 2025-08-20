//! "Values" represent typed ports in the jeff language.
//!
//! Internally, these are coalesced into a single array at the function
//! definition and each port contains an index into this array.

use crate::capnp::jeff_capnp;

/// Value type.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Type {
    /// Quantum bit.
    ///
    /// Qubits are linear types.
    Qubit,
    /// Quantum registers.
    ///
    /// A quantum register is an array of slots that can hold qubits.
    /// Slots of a quantum register can either be empty or filled with a qubit.
    ///
    /// Quantum registers are linear types.
    ///
    /// The length of the register is not known at compile time, but fixed at runtime.
    QubitRegister,
    /// Integers.
    ///
    /// The type does not distinguish between signed and unsigned integers.
    /// Instead it is up to the operation to interpret the integer as signed or unsigned.
    /// Signed integers are represented using two's complement.
    ///
    /// Integers of bitwidth 1 can be used as classical bits or boolean values.
    Int {
        /// Bitwidth of the integer.
        bits: u8,
    },
    /// Integer array.
    ///
    /// The length of the array is not known at compile time, but fixed at runtime.
    ///
    /// Arrays of integers of bitwidth 1 can be used as classical bit arrays.
    IntArray {
        /// Bitwidth of the integers.
        bits: u8,
    },
    /// Floating point numbers.
    Float {
        /// Precision of the floating point number.
        precision: FloatPrecision,
    },
    /// Array of floating point numbers.
    ///
    /// The length of the array is not known at compile time, but fixed at runtime.
    FloatArray {
        /// Precision of the floating point numbers.
        precision: FloatPrecision,
    },
}

impl Type {
    /// Create a new integer type.
    pub fn int(bits: u8) -> Self {
        Self::Int { bits }
    }

    /// Create a new boolean type.
    pub fn bool() -> Self {
        Self::Int { bits: 1 }
    }

    /// Create a new integer array type.
    pub fn int_array(bits: u8) -> Self {
        Self::IntArray { bits }
    }

    /// Create a new floating point type.
    pub fn float(precision: FloatPrecision) -> Self {
        Self::Float { precision }
    }

    /// Create a new floating point array type.
    pub fn float_array(precision: FloatPrecision) -> Self {
        Self::FloatArray { precision }
    }

    /// Parse a type from a capnp reader.
    pub(crate) fn read_capnp(reader: jeff_capnp::type_::Reader<'_>) -> Self {
        use jeff_capnp::type_::Which;
        match reader
            .which()
            .expect("Type id was not in the schema. Schema should have been verified.")
        {
            Which::Qubit(_) => Self::Qubit,
            Which::Qureg(_) => Self::QubitRegister,
            Which::Int(bits) => Self::Int { bits },
            Which::IntArray(bits) => Self::IntArray { bits },
            Which::Float(prec) => Self::Float {
                precision: FloatPrecision::from_capnp(prec.expect(
                    "FloatPrecision id was not in the schema. Schema should have been verified.",
                )),
            },
            Which::FloatArray(prec) => Self::FloatArray {
                precision: FloatPrecision::from_capnp(prec.expect(
                    "FloatPrecision id was not in the schema. Schema should have been verified.",
                )),
            },
        }
    }

    /// Build a capnp type from this type.
    #[allow(unused)]
    pub(crate) fn build_capnp(&self, mut builder: jeff_capnp::type_::Builder) {
        match self {
            Self::Qubit => builder.set_qubit(()),
            Self::QubitRegister => builder.set_qureg(()),
            Self::Int { bits } => builder.set_int(*bits),
            Self::IntArray { bits } => builder.set_int_array(*bits),
            Self::Float { precision } => builder.set_float(precision.as_capnp()),
            Self::FloatArray { precision } => builder.set_float_array(precision.as_capnp()),
        }
    }
}

/// Precision of floating point number.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FloatPrecision {
    /// 32-bit floating point number.
    Float32,
    /// 64-bit floating point number.
    Float64,
}

impl FloatPrecision {
    /// Parse a float precision from a capnp reader.
    pub(crate) fn from_capnp(reader: jeff_capnp::FloatPrecision) -> Self {
        match reader {
            jeff_capnp::FloatPrecision::Float32 => Self::Float32,
            jeff_capnp::FloatPrecision::Float64 => Self::Float64,
        }
    }

    /// Returns the capnp representation of this float precision.
    pub(crate) fn as_capnp(&self) -> jeff_capnp::FloatPrecision {
        match self {
            Self::Float32 => jeff_capnp::FloatPrecision::Float32,
            Self::Float64 => jeff_capnp::FloatPrecision::Float64,
        }
    }

    /// Returns the bitwidth of the floating point number.
    pub fn bits(self) -> u8 {
        match self {
            Self::Float32 => 32,
            Self::Float64 => 64,
        }
    }
}
