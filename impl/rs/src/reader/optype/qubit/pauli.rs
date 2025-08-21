//! Definitions for the Pauli-product rotation gate.

use itertools::Itertools;

use crate::jeff_capnp;

/// An arbitrary Pauli-product rotation gate, composed of a list of Pauli operators.
///
/// The operation is characterized by a rotation angle `θ` and a Pauli tensor product `P`:
///
/// ```text
/// PPR(θ) = exp(iθP),  P = P₁ ⊗ P₂ ⊗ ... ⊗ Pₙ
/// ```
#[derive(Clone, Copy, Debug, derive_more::Display)]
#[display("PauliString({paulis})", paulis = self.iter().map(|p| p.name()).join(""))]
pub struct PauliString<'a> {
    /// List reader over the Pauli operators.
    paulis: capnp::enum_list::Reader<'a, jeff_capnp::Pauli>,
}

/// A Pauli operator.
#[derive(Clone, Copy, Debug, derive_more::Display)]
#[display("Pauli({pauli})", pauli = self.name())]
pub enum Pauli {
    /// Pauli-X operator.
    X,
    /// Pauli-Y operator.
    Y,
    /// Pauli-Z operator.
    Z,
    /// Identity operator.
    I,
}

impl<'a> PauliString<'a> {
    /// Create a new Pauli string from a capnp reader.
    pub(super) fn read_capnp(
        pauli_string: capnp::enum_list::Reader<'a, jeff_capnp::Pauli>,
    ) -> Self {
        Self {
            paulis: pauli_string,
        }
    }

    /// Returns the number of Pauli operators in this string.
    pub fn len(&self) -> usize {
        self.paulis.len() as usize
    }

    /// Returns `true` if this string is empty.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Returns the `n`-th Pauli operator in this string.
    pub fn get(&self, n: usize) -> Pauli {
        let pauli = self
            .paulis
            .get(n as u32)
            .expect("Pauli operator should be present");
        Pauli::read_capnp(pauli)
    }

    /// Returns an iterator over the Pauli operators in this string.
    pub fn iter(&self) -> impl Iterator<Item = Pauli> + 'a {
        self.paulis
            .iter()
            .map(|p| Pauli::read_capnp(p.expect("Invalid Pauli operator")))
    }

    /// Returns the number of qubits that the gate acts on.
    pub fn num_qubits(&self) -> usize {
        self.len()
    }

    /// Returns the number of floating point parameters that the gate takes as inputs.
    pub fn num_params(&self) -> usize {
        1
    }
}

impl Pauli {
    /// Create a new well-known gate type from a capnp reader.
    pub(self) fn read_capnp(pauli: jeff_capnp::Pauli) -> Self {
        match pauli {
            jeff_capnp::Pauli::X => Self::X,
            jeff_capnp::Pauli::Y => Self::Y,
            jeff_capnp::Pauli::Z => Self::Z,
            jeff_capnp::Pauli::I => Self::I,
            #[allow(unreachable_patterns)]
            _ => unimplemented!(),
        }
    }

    /// Returns a string representation of the Pauli operator.
    pub fn name(&self) -> &'static str {
        match self {
            Self::X => "X",
            Self::Y => "Y",
            Self::Z => "Z",
            Self::I => "I",
        }
    }
}
