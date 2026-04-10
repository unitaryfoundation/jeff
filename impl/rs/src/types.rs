//! "Values" represent typed ports in the jeff language.
//!
//! Internally, these are coalesced into a single array at the function
//! definition and each port contains an index into this array.

use crate::capnp::jeff_capnp;
use derive_more::Display;

/// Value type.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Display)]
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
    /// If `length` is `None`, the register has dynamic length.
    /// If `Some`, the register has static compile-time length.
    #[display("Qureg[{}]", length.map_or("?".to_string(), |l| l.to_string()))]
    QubitRegister {
        /// Optional compile-time length.
        length: Option<u32>,
    },
    /// Integers.
    ///
    /// The type does not distinguish between signed and unsigned integers.
    /// Instead it is up to the operation to interpret the integer as signed or unsigned.
    /// Signed integers are represented using two's complement.
    ///
    /// Integers of bitwidth 1 can be used as classical bits or boolean values.
    #[display("Int{}", bits)]
    Int {
        /// Bitwidth of the integer.
        bits: u8,
    },
    /// Integer array.
    ///
    /// Arrays of integers of bitwidth 1 can be used as classical bit arrays.
    ///
    /// If `length` is `None`, the array has dynamic length.
    /// If `Some`, the array has static compile-time length.
    #[display("IntArray{}[{}]", bits, length.map_or("?".to_string(), |l| l.to_string()))]
    IntArray {
        /// Bitwidth of the integers.
        bits: u8,
        /// Optional compile-time length.
        length: Option<u32>,
    },
    /// Floating point numbers.
    #[display("Float{}", precision.bits())]
    Float {
        /// Precision of the floating point number.
        precision: FloatPrecision,
    },
    /// Array of floating point numbers.
    ///
    /// If `length` is `None`, the array has dynamic length.
    /// If `Some`, the array has static compile-time length.
    #[display("FloatArray{}[{}]", precision.bits(), length.map_or("?".to_string(), |l| l.to_string()))]
    FloatArray {
        /// Precision of the floating point numbers.
        precision: FloatPrecision,
        /// Optional compile-time length.
        length: Option<u32>,
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
    ///
    /// If `length` is `None`, the array has dynamic length.
    /// If `Some`, the array has static compile-time length.
    pub fn int_array(bits: u8, length: Option<u32>) -> Self {
        Self::IntArray { bits, length }
    }

    /// Create a new floating point type.
    pub fn float(precision: FloatPrecision) -> Self {
        Self::Float { precision }
    }

    /// Create a new floating point array type.
    ///
    /// If `length` is `None`, the array has dynamic length.
    /// If `Some`, the array has static compile-time length.
    pub fn float_array(precision: FloatPrecision, length: Option<u32>) -> Self {
        Self::FloatArray { precision, length }
    }

    /// Parse a type from a capnp reader.
    pub(crate) fn read_capnp(reader: jeff_capnp::type_::Reader<'_>) -> Self {
        use jeff_capnp::type_::Which;
        match reader
            .which()
            .expect("Type id was not in the schema. Schema should have been verified.")
        {
            Which::Qubit(_) => Self::Qubit,
            Which::Qureg(qureg) => Self::QubitRegister {
                length: match qureg.which().expect(
                    "Qureg type id was not in the schema. Schema should have been verified.",
                ) {
                    jeff_capnp::type_::qureg::Which::Static(length) => Some(length),
                    jeff_capnp::type_::qureg::Which::Dynamic(_) => None,
                },
            },
            Which::Int(bits) => Self::Int { bits },
            Which::IntArray(int_array) => Self::IntArray {
                bits: int_array.get_bitwidth(),
                length: match int_array.get_length().which().expect(
                    "IntArray length id was not in the schema. Schema should have been verified.",
                ) {
                    jeff_capnp::type_::int_array::length::Which::Static(length) => Some(length),
                    jeff_capnp::type_::int_array::length::Which::Dynamic(_) => None,
                },
            },
            Which::Float(prec) => Self::Float {
                precision: FloatPrecision::from_capnp(prec.expect(
                    "FloatPrecision id was not in the schema. Schema should have been verified.",
                )),
            },
            Which::FloatArray(float_array) => Self::FloatArray {
                precision: FloatPrecision::from_capnp(float_array.get_precision().expect(
                    "FloatPrecision id was not in the schema. Schema should have been verified.",
                )),
                length: match float_array.get_length().which().expect(
                    "FloatArray length id was not in the schema. Schema should have been verified.",
                ) {
                    jeff_capnp::type_::float_array::length::Which::Static(length) => Some(length),
                    jeff_capnp::type_::float_array::length::Which::Dynamic(_) => None,
                },
            },
        }
    }

    /// Build a capnp type from this type.
    #[allow(unused)]
    pub(crate) fn build_capnp(&self, mut builder: jeff_capnp::type_::Builder) {
        match self {
            Self::Qubit => builder.set_qubit(()),
            Self::QubitRegister { length } => {
                let mut qureg = builder.reborrow().init_qureg();
                match length {
                    Some(length) => qureg.set_static(*length),
                    None => qureg.set_dynamic(()),
                }
            }
            Self::Int { bits } => builder.set_int(*bits),
            Self::IntArray { bits, length } => {
                let mut int_array = builder.reborrow().init_int_array();
                int_array.set_bitwidth(*bits);
                let mut int_array_len = int_array.reborrow().init_length();
                match length {
                    Some(length) => int_array_len.set_static(*length),
                    None => int_array_len.set_dynamic(()),
                }
            }
            Self::Float { precision } => builder.set_float(precision.as_capnp()),
            Self::FloatArray { precision, length } => {
                let mut float_array = builder.reborrow().init_float_array();
                float_array.set_precision(precision.as_capnp());
                let mut float_array_len = float_array.reborrow().init_length();
                match length {
                    Some(length) => float_array_len.set_static(*length),
                    None => float_array_len.set_dynamic(()),
                }
            }
        }
    }
}

/// Precision of floating point number.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Display)]
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
