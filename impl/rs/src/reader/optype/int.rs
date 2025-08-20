//! Integer operations

use crate::jeff_capnp;

use super::ConstArray;

/// An operation over integers.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum IntOp {
    /// Create a constant 1 bit integer.
    Const1(bool),
    /// Create a constant 8 bit integer.
    Const8(u8),
    /// Create a constant 16 bit integer.
    Const16(u16),
    /// Create a constant 32 bit integer.
    Const32(u32),
    /// Create a constant 64 bit integer.
    Const64(u64),
    /// Add two integers.
    Add,
    /// Subtract two integers.
    Sub,
    /// Multiply two integers.
    Mul,
    /// Divide two signed integers.
    DivS,
    /// Divide two unsigned integers.
    DivU,
    /// Take the power of an integer.
    Pow,
    /// Logical bitwise AND.
    And,
    /// Logical bitwise OR.
    Or,
    /// Logical bitwise XOR.
    Xor,
    /// Logical bitwise NOT.
    Not,
    /// Minimum of two signed integers.
    MinS,
    /// Minimum of two unsigned integers.
    MinU,
    /// Maximum of two signed integers.
    MaxS,
    /// Maximum of two unsigned integers.
    MaxU,
    /// Test two integers for equality.
    Eq,
    /// Check if one signed integer is strictly less than another.
    LtS,
    /// Check if one signed integer is less than or equal to another.
    LteS,
    /// Check if one unsigned integer is strictly less than another.
    LtU,
    /// Check if one unsigned integer is less than or equal to another.
    LteU,
    /// Take the absolute value of a signed integer.
    Abs,
    /// Remainder of a division of two signed integers.
    RemS,
    /// Remainder of a division of two unsigned integers.
    RemU,
    /// Logical shift left.
    Shl,
    /// Logical shift right.
    Shr,
}

/// An operation over integer arrays.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum IntArrayOp<'a> {
    /// Create a constant 1 bit integer array.
    ConstArray1(ConstArray<'a, bool>),
    /// Create a constant 8 bit integer array.
    ConstArray8(ConstArray<'a, u8>),
    /// Create a constant 16 bit integer array.
    ConstArray16(ConstArray<'a, u16>),
    /// Create a constant 32 bit integer array.
    ConstArray32(ConstArray<'a, u32>),
    /// Create a constant 64 bit integer array.
    ConstArray64(ConstArray<'a, u64>),
    /// Create a zeroed integer array of a given bitwidth with dynamic length.
    Zero {
        /// The number of bits in each integer in the array.
        bits: u8,
    },
    /// Get the value of an integer array at a given index.
    GetIndex,
    /// Set the value of an integer array at a given index.
    SetIndex,
    /// Get the length of an integer array.
    Length,
    /// Creates an integer array from a variable number of input values.
    Create,
}

impl IntOp {
    /// Create a new integer operation from a capnp reader.
    pub(crate) fn read_capnp(int_op: jeff_capnp::int_op::Reader<'_>) -> Self {
        match int_op.which().expect("Integer operation should be present") {
            jeff_capnp::int_op::Which::Const1(val) => Self::Const1(val),
            jeff_capnp::int_op::Which::Const8(val) => Self::Const8(val),
            jeff_capnp::int_op::Which::Const16(val) => Self::Const16(val),
            jeff_capnp::int_op::Which::Const32(val) => Self::Const32(val),
            jeff_capnp::int_op::Which::Const64(val) => Self::Const64(val),
            jeff_capnp::int_op::Which::Add(()) => Self::Add,
            jeff_capnp::int_op::Which::Sub(()) => Self::Sub,
            jeff_capnp::int_op::Which::Mul(()) => Self::Mul,
            jeff_capnp::int_op::Which::DivS(()) => Self::DivS,
            jeff_capnp::int_op::Which::DivU(()) => Self::DivU,
            jeff_capnp::int_op::Which::Pow(()) => Self::Pow,
            jeff_capnp::int_op::Which::And(()) => Self::And,
            jeff_capnp::int_op::Which::Or(()) => Self::Or,
            jeff_capnp::int_op::Which::Xor(()) => Self::Xor,
            jeff_capnp::int_op::Which::Not(()) => Self::Not,
            jeff_capnp::int_op::Which::MinS(()) => Self::MinS,
            jeff_capnp::int_op::Which::MinU(()) => Self::MinU,
            jeff_capnp::int_op::Which::MaxS(()) => Self::MaxS,
            jeff_capnp::int_op::Which::MaxU(()) => Self::MaxU,
            jeff_capnp::int_op::Which::Eq(()) => Self::Eq,
            jeff_capnp::int_op::Which::LtS(()) => Self::LtS,
            jeff_capnp::int_op::Which::LteS(()) => Self::LteS,
            jeff_capnp::int_op::Which::LtU(()) => Self::LtU,
            jeff_capnp::int_op::Which::LteU(()) => Self::LteU,
            jeff_capnp::int_op::Which::Abs(()) => Self::Abs,
            jeff_capnp::int_op::Which::RemS(()) => Self::RemS,
            jeff_capnp::int_op::Which::RemU(()) => Self::RemU,
            jeff_capnp::int_op::Which::Shl(()) => Self::Shl,
            jeff_capnp::int_op::Which::Shr(()) => Self::Shr,
        }
    }
}

impl<'a> IntArrayOp<'a> {
    /// Create a new integer array operation from a capnp reader.
    pub(crate) fn read_capnp(int_array_op: jeff_capnp::int_array_op::Reader<'a>) -> Self {
        match int_array_op
            .which()
            .expect("Integer array operation should be present")
        {
            jeff_capnp::int_array_op::Which::Const1(val) => Self::ConstArray1(
                ConstArray::read_capnp(val.expect("Const1 should be present")),
            ),
            jeff_capnp::int_array_op::Which::Const8(val) => Self::ConstArray8(
                ConstArray::read_capnp(val.expect("Const8 should be present")),
            ),
            jeff_capnp::int_array_op::Which::Const16(val) => Self::ConstArray16(
                ConstArray::read_capnp(val.expect("Const16 should be present")),
            ),
            jeff_capnp::int_array_op::Which::Const32(val) => Self::ConstArray32(
                ConstArray::read_capnp(val.expect("Const32 should be present")),
            ),
            jeff_capnp::int_array_op::Which::Const64(val) => Self::ConstArray64(
                ConstArray::read_capnp(val.expect("Const64 should be present")),
            ),
            jeff_capnp::int_array_op::Which::Zero(val) => Self::Zero { bits: val },
            jeff_capnp::int_array_op::Which::GetIndex(()) => Self::GetIndex,
            jeff_capnp::int_array_op::Which::SetIndex(()) => Self::SetIndex,
            jeff_capnp::int_array_op::Which::Length(()) => Self::Length,
            jeff_capnp::int_array_op::Which::Create(()) => Self::Create,
        }
    }
}
