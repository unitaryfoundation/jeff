//! Floating point operations

use super::ConstArray;
use crate::jeff_capnp;
use crate::types::FloatPrecision;

/// An operation over floating point numbers.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum FloatOp {
    /// Create a constant 32 bit float.
    Const32(f32),
    /// Create a constant 64 bit float.
    Const64(f64),
    /// Add two floats.
    Add,
    /// Subtract two floats.
    Sub,
    /// Multiply two floats.
    Mul,
    /// Calculate one float raised to the power of another.
    Pow,
    /// Test two floats for equality.
    Eq,
    /// Check if one float is strictly less than another.
    Lt,
    /// Check if one float is less than or equal to another.
    Lte,
    /// Calculate the square root of a float.
    Sqrt,
    /// Calculate the absolute value of a float.
    Abs,
    /// Round a float up to the nearest integer.
    Ceil,
    /// Round a float down to the nearest integer.
    Floor,
    /// Check if a float is NaN.
    IsNan,
    /// Check if a float is infinite.
    IsInf,
    /// Calculate e raised to the power of a float.
    Exp,
    /// Calculate the natural logarithm of a float.
    Log,
    /// Calculate the sine of a float.
    Sin,
    /// Calculate the cosine of a float.
    Cos,
    /// Calculate the tangent of a float.
    Tan,
    /// Calculate the arcsine of a float.
    Asin,
    /// Calculate the arccosine of a float.
    Acos,
    /// Calculate the arctangent of a float.
    Atan,
    /// Calculate the 2-argument arctangent.
    Atan2,
    /// Calculate the hyperbolic sine of a float.
    Sinh,
    /// Calculate the hyperbolic cosine of a float.
    Cosh,
    /// Calculate the hyperbolic tangent of a float.
    Tanh,
    /// Calculate the inverse hyperbolic sine of a float.
    Asinh,
    /// Calculate the inverse hyperbolic cosine of a float.
    Acosh,
    /// Calculate the inverse hyperbolic tangent of a float.
    Atanh,
    /// Maximum of two floats.
    Max,
    /// Minimum of two floats.
    Min,
}

/// An operation over floating point arrays.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum FloatArrayOp<'a> {
    /// Create a constant 32 bit float array.
    Const32(ConstArray<'a, f32>),
    /// Create a constant 64 bit float array.
    Const64(ConstArray<'a, f64>),
    /// Create a zeroed float array of a given precision with dynamic length.
    Zero {
        /// The precision of the floats in the array.
        precision: FloatPrecision,
    },
    /// Get the value of a float array at a given index.
    GetIndex,
    /// Set the value of a float array at a given index.
    SetIndex,
    /// Get the length of a float array.
    Length,
    /// Creates a float array from a variable number of input values.
    Create,
}

impl FloatOp {
    /// Create a new floating point operation from a capnp reader.
    pub(crate) fn read_capnp(float_op: jeff_capnp::float_op::Reader<'_>) -> Self {
        match float_op.which().expect("Float operation should be present") {
            jeff_capnp::float_op::Which::Const32(val) => Self::Const32(val),
            jeff_capnp::float_op::Which::Const64(val) => Self::Const64(val),
            jeff_capnp::float_op::Which::Add(()) => Self::Add,
            jeff_capnp::float_op::Which::Sub(()) => Self::Sub,
            jeff_capnp::float_op::Which::Mul(()) => Self::Mul,
            jeff_capnp::float_op::Which::Pow(()) => Self::Pow,
            jeff_capnp::float_op::Which::Eq(()) => Self::Eq,
            jeff_capnp::float_op::Which::Lt(()) => Self::Lt,
            jeff_capnp::float_op::Which::Lte(()) => Self::Lte,
            jeff_capnp::float_op::Which::Sqrt(()) => Self::Sqrt,
            jeff_capnp::float_op::Which::Abs(()) => Self::Abs,
            jeff_capnp::float_op::Which::Ceil(()) => Self::Ceil,
            jeff_capnp::float_op::Which::Floor(()) => Self::Floor,
            jeff_capnp::float_op::Which::IsNan(()) => Self::IsNan,
            jeff_capnp::float_op::Which::IsInf(()) => Self::IsInf,
            jeff_capnp::float_op::Which::Exp(()) => Self::Exp,
            jeff_capnp::float_op::Which::Log(()) => Self::Log,
            jeff_capnp::float_op::Which::Sin(()) => Self::Sin,
            jeff_capnp::float_op::Which::Cos(()) => Self::Cos,
            jeff_capnp::float_op::Which::Tan(()) => Self::Tan,
            jeff_capnp::float_op::Which::Asin(()) => Self::Asin,
            jeff_capnp::float_op::Which::Acos(()) => Self::Acos,
            jeff_capnp::float_op::Which::Atan(()) => Self::Atan,
            jeff_capnp::float_op::Which::Atan2(()) => Self::Atan2,
            jeff_capnp::float_op::Which::Sinh(()) => Self::Sinh,
            jeff_capnp::float_op::Which::Cosh(()) => Self::Cosh,
            jeff_capnp::float_op::Which::Tanh(()) => Self::Tanh,
            jeff_capnp::float_op::Which::Asinh(()) => Self::Asinh,
            jeff_capnp::float_op::Which::Acosh(()) => Self::Acosh,
            jeff_capnp::float_op::Which::Atanh(()) => Self::Atanh,
            jeff_capnp::float_op::Which::Max(()) => Self::Max,
            jeff_capnp::float_op::Which::Min(()) => Self::Min,
        }
    }
}

impl<'a> FloatArrayOp<'a> {
    /// Create a new floating point array operation from a capnp reader.
    pub(crate) fn read_capnp(float_array_op: jeff_capnp::float_array_op::Reader<'a>) -> Self {
        match float_array_op
            .which()
            .expect("Float array operation should be present")
        {
            jeff_capnp::float_array_op::Which::Const32(val) => Self::Const32(
                ConstArray::read_capnp(val.expect("Const32 should be present")),
            ),
            jeff_capnp::float_array_op::Which::Const64(val) => Self::Const64(
                ConstArray::read_capnp(val.expect("Const64 should be present")),
            ),
            jeff_capnp::float_array_op::Which::Zero(precision) => Self::Zero {
                precision: FloatPrecision::from_capnp(
                    precision.expect("Precision should be present"),
                ),
            },
            jeff_capnp::float_array_op::Which::GetIndex(()) => Self::GetIndex,
            jeff_capnp::float_array_op::Which::SetIndex(()) => Self::SetIndex,
            jeff_capnp::float_array_op::Which::Length(()) => Self::Length,
            jeff_capnp::float_array_op::Which::Create(()) => Self::Create,
        }
    }
}
