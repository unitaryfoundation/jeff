//! Definitions for the well-known gates with well-defined semantics.

use crate::jeff_capnp;

/// Well-known quantum gates.
#[derive(Clone, Copy, Debug, Default, derive_more::Display)]
#[non_exhaustive]
pub enum WellKnownGate {
    /// Global phase operation on the "vacuum" state (no qubits).
    ///
    /// ```text
    /// G = | exp(iθ) |
    /// ```
    ///
    /// Inputs:
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * No outputs
    GPhase,
    /// Identity (no-op) gate on a single qubit.
    ///
    /// ```text
    /// I = | 1  0 |
    ///     | 0  1 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    #[default]
    I,
    /// Pauli-X gate. Also known as the NOT gate.
    ///
    /// ```text
    /// X = | 0  1 |
    ///     | 1  0 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    X,
    /// Pauli-Y gate.
    ///
    /// ```text
    /// Y = | 0  -i |
    ///     | i   0 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Y,
    /// Pauli-Z gate.
    ///
    /// ```text
    /// Z = | 1   0 |
    ///     | 0  -1 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Z,
    /// S gate.
    ///
    /// ```text
    /// S = | 1   0 |
    ///     | 0   i |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    S,
    /// T gate.
    ///
    /// ```text
    /// T = | 1   0        |
    ///     | 0   exp(iπ/4)|
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    T,
    /// Rotation around the |1> state.
    ///
    /// ```text
    /// R1(θ) = | 1   0       |
    ///         | 0   exp(iθ) |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    R1,
    /// Rotation around the X axis.
    ///
    /// ```text
    /// Rx(θ) = |  cos(θ/2)  -isin(θ/2) |
    ///         | -isin(θ/2)  cos(θ/2)  |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Rx,
    /// Rotation around the Y axis.
    ///
    /// ```text
    /// Ry(θ) = |  cos(θ/2)  -sin(θ/2) |
    ///         |  sin(θ/2)   cos(θ/2) |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Ry,
    /// Rotation around the Z axis.
    ///
    /// ```text
    /// Rz(θ) = | exp(-iθ/2)   0         |
    ///         | 0            exp(iθ/2) |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Rz,
    /// Hadamard gate.
    ///
    /// ```text
    /// H = 1/√2 | 1   1 |
    ///          | 1  -1 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    H,
    /// Euler gate.
    ///
    /// ```text
    /// U(θ,φ,λ) = | cos(θ/2)          -exp(iλ)sin(θ/2)    |
    ///           | exp(iφ)sin(θ/2)   exp(iλ)cos(θ/2)       |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    /// * [`Float`][crate::types::Type::Float] rotation in radians.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    U,
    /// Swap gate. Swaps the state of two qubits.
    ///
    /// ```text
    /// Swap = | 1   0   0   0 |
    ///        | 0   0   1   0 |
    ///        | 0   1   0   0 |
    ///        | 0   0   0   1 |
    /// ```
    ///
    /// Inputs:
    /// * [`Qubit`][crate::types::Type::Qubit] to act on.
    ///
    /// Outputs:
    /// * [`Qubit`][crate::types::Type::Qubit] acted on.
    Swap,
}

impl WellKnownGate {
    /// Create a new well-known gate type from a capnp reader.
    pub(super) fn read_capnp(well_known: jeff_capnp::WellKnownGate) -> Self {
        match well_known {
            jeff_capnp::WellKnownGate::Gphase => Self::GPhase,
            jeff_capnp::WellKnownGate::I => Self::I,
            jeff_capnp::WellKnownGate::X => Self::X,
            jeff_capnp::WellKnownGate::Y => Self::Y,
            jeff_capnp::WellKnownGate::Z => Self::Z,
            jeff_capnp::WellKnownGate::S => Self::S,
            jeff_capnp::WellKnownGate::T => Self::T,
            jeff_capnp::WellKnownGate::R1 => Self::R1,
            jeff_capnp::WellKnownGate::Rx => Self::Rx,
            jeff_capnp::WellKnownGate::Ry => Self::Ry,
            jeff_capnp::WellKnownGate::Rz => Self::Rz,
            jeff_capnp::WellKnownGate::H => Self::H,
            jeff_capnp::WellKnownGate::U => Self::U,
            jeff_capnp::WellKnownGate::Swap => Self::Swap,
        }
    }

    /// Returns the number of qubits that the gate acts on.
    #[inline]
    #[must_use]
    pub fn num_qubits(&self) -> usize {
        use WellKnownGate::*;

        match self {
            GPhase => 0,
            I | X | Y | Z | S | T | R1 | Rx | Ry | Rz | H | U => 1,
            Swap => 2,
        }
    }

    /// Returns the number of floating point parameters that the gate takes as inputs.
    #[inline]
    #[must_use]
    pub fn num_params(&self) -> usize {
        use WellKnownGate::*;

        match self {
            I | X | Y | Z | S | T | H | Swap => 0,
            GPhase | R1 | Rx | Ry | Rz => 1,
            U => 3,
        }
    }
}
