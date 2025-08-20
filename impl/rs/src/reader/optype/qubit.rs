//! Qubit operations

use crate::jeff_capnp;
use crate::reader::string_table::StringTable;
use crate::reader::ReadError;

/// An operation over qubits.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum QubitOp<'a> {
    /// Allocates a new qubit in the |0> state.
    Alloc,
    /// Frees a qubit.
    ///
    /// This operation makes no assumptions about the state of the qubit.
    Free,
    /// Frees a qubit in the |0> state.
    ///
    /// This operation can be used to avoid performing resets when it is known
    /// that the qubit has already been reset. It is undefined behavior to free
    /// a qubit that is not in the |0> state.
    FreeZero,
    /// Perform a destructive measurement of a qubit in the computational basis.
    Measure,
    /// Perform a non-destructive measurement of a qubit in the computational basis.
    MeasureNd,
    /// Resets a qubit to the |0> state.
    Reset,
    /// Apply a quantum gate.
    Gate(GateOp<'a>),
}

/// An operation over qubit registers.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub enum QubitRegisterOp {
    /// Allocates a new qubit register given a number of qubits in the |0> state.
    Alloc = 0,
    /// Frees a qubit register.
    ///
    /// This operation makes no assumptions about the state of the qubits.
    Free = 10,
    /// Frees a qubit register, assuming that all qubits are in the |0> state.
    ///
    /// It is undefined behavior to free a qubit register containing qubits that are not in the |0> state.
    FreeZero = 1,
    /// Extracts a single qubit from a qubit register.
    ///
    /// The slot must have been filled before and is marked as empty after the extraction.
    ExtractIndex,
    /// Insert a single qubit into a qubit register.
    ///
    /// The slot must have been empty before and is marked as filled after the insertion.
    InsertIndex,
    /// Extract a slice of qubits from a qubit register given a range of indices.
    ///
    /// All slots in the range are marked as empty in the original register.
    ExtractSlice,
    /// Insert a slice of qubits into a qubit register.
    ///
    /// All slots in the inserted range in the original register must have been empty.
    InsertSlice,
    /// Returns the length of the qubit register.
    Length,
    /// Splits a qubit register into two qubit registers at a given index.
    Split,
    /// Joins together two qubit registers into a single qubit register.
    Join,
    /// Creates a qubit register from a variable number of input qubits.
    Create,
}

/// Quantum gate operation.
#[derive(Clone, Copy, Debug)]
#[non_exhaustive]
pub struct GateOp<'a> {
    /// The type of gate.
    pub gate_type: GateOpType<'a>,
    /// The number of control qubits for gate.
    pub control_qubits: u8,
    /// Whether to apply the adjoint of the named gate.
    pub adjoint: bool,
    /// A number of times to apply this gate in sequence.
    pub power: u8,
}

/// The type of gate operation.
#[derive(Clone, Copy, Debug)]
pub enum GateOpType<'a> {
    /// A custom gate.
    Custom {
        /// The name of the gate.
        name: &'a str,
        /// The number of qubits the gate acts on.
        num_qubits: u8,
        /// The number of floating point parameters that the gate takes as inputs,
        /// after the qubit values.
        num_params: u8,
    },
    /// A gate in the common shared gate set.
    ///
    /// Use [`GateOpType::Custom`] for gates not in the shared set.
    WellKnown(WellKnownGate),
    /// An arbitrary Pauli-product rotation gate.
    ///
    /// Use [`GateOpType::Custom`] for gates not in the shared set.
    PauliProdRotation {
        /// Pauli string
        pauli_string: PauliString<'a>,
    },
}

/// A Pauli operator.
#[derive(Clone, Copy, Debug)]
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

/// A Pauli string, composed of a list of [Pauli] operators.
#[derive(Clone, Copy, Debug)]
pub struct PauliString<'a> {
    /// List reader over the Pauli operators.
    paulis: capnp::enum_list::Reader<'a, jeff_capnp::Pauli>,
}

/// Well-known quantum gates.
#[derive(Clone, Copy, Debug)]
pub enum WellKnownGate {
    /// Pauli-X gate.
    X,
    /// Pauli-Y gate.
    Y,
    /// Pauli-Z gate.
    Z,
    /// S gate.
    S,
    /// T gate.
    T,
    /// R1 gate.
    R1,
    /// Rx gate.
    Rx,
    /// Ry gate.
    Ry,
    /// Rz gate.
    Rz,
    /// Hadamard gate.
    H,
    /// U gate.
    U,
    /// Swap gate.
    Swap,
}

impl<'a> QubitOp<'a> {
    /// Create a new qubit operation from a capnp reader.
    pub(crate) fn read_capnp(
        qubit_op: jeff_capnp::qubit_op::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Self {
        match qubit_op.which().expect("Qubit operation should be present") {
            jeff_capnp::qubit_op::Which::Alloc(()) => Self::Alloc,
            jeff_capnp::qubit_op::Which::Free(()) => Self::Free,
            jeff_capnp::qubit_op::Which::FreeZero(()) => Self::FreeZero,
            jeff_capnp::qubit_op::Which::Measure(()) => Self::Measure,
            jeff_capnp::qubit_op::Which::MeasureNd(()) => Self::MeasureNd,
            jeff_capnp::qubit_op::Which::Reset(()) => Self::Reset,
            jeff_capnp::qubit_op::Which::Gate(gate) => {
                Self::Gate(GateOp::read_capnp(gate.unwrap(), strings))
            }
            #[allow(unreachable_patterns)]
            _ => unimplemented!(),
        }
    }
}

impl QubitRegisterOp {
    /// Create a new qubit register operation from a capnp reader.
    pub(crate) fn read_capnp(qubit_reg_op: jeff_capnp::qureg_op::Reader<'_>) -> Self {
        match qubit_reg_op
            .which()
            .expect("Qubit register operation should be present")
        {
            jeff_capnp::qureg_op::Which::Alloc(()) => Self::Alloc,
            jeff_capnp::qureg_op::Which::Free(()) => Self::Free,
            jeff_capnp::qureg_op::Which::FreeZero(()) => Self::FreeZero,
            jeff_capnp::qureg_op::Which::ExtractIndex(()) => Self::ExtractIndex,
            jeff_capnp::qureg_op::Which::InsertIndex(()) => Self::InsertIndex,
            jeff_capnp::qureg_op::Which::ExtractSlice(()) => Self::ExtractSlice,
            jeff_capnp::qureg_op::Which::InsertSlice(()) => Self::InsertSlice,
            jeff_capnp::qureg_op::Which::Length(()) => Self::Length,
            jeff_capnp::qureg_op::Which::Split(()) => Self::Split,
            jeff_capnp::qureg_op::Which::Join(()) => Self::Join,
            jeff_capnp::qureg_op::Which::Create(()) => Self::Create,
            #[allow(unreachable_patterns)]
            _ => unimplemented!(),
        }
    }
}

impl<'a> GateOp<'a> {
    /// Create a new gate operation.
    ///
    /// # Panics
    ///
    /// Panics if the gate name index is out of bounds or the string is not valid utf8.
    pub(crate) fn read_capnp(
        gate: jeff_capnp::qubit_gate::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Self {
        Self::try_read_capnp(gate, strings).unwrap_or_else(|e| panic!("{}", e))
    }

    /// Create a new gate operation from a capnp reader.
    ///
    /// # Errors
    ///
    /// - [`ReadError::StringOutOfBounds`] if the gate name index is out of bounds.
    /// - [`ReadError::StringNotUtf8`] if the gate name index is not valid utf8.
    pub(crate) fn try_read_capnp(
        gate: jeff_capnp::qubit_gate::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Result<Self, ReadError> {
        let control_qubits = gate.get_control_qubits();
        let adjoint = gate.get_adjoint();
        let power = gate.get_power();
        let gate_type = match gate.which().expect("Gate type should be present") {
            jeff_capnp::qubit_gate::Which::WellKnown(well_known) => {
                let well_known =
                    WellKnownGate::read_capnp(well_known.expect("Unsupported well-known gate"));
                GateOpType::WellKnown(well_known)
            }
            jeff_capnp::qubit_gate::Which::Custom(custom) => {
                let name = strings.get(custom.get_name(), "gate name")?;
                let num_qubits = custom.get_num_qubits();
                let num_params = custom.get_num_params();

                GateOpType::Custom {
                    name,
                    num_qubits,
                    num_params,
                }
            }
            jeff_capnp::qubit_gate::Which::Ppr(ppr) => {
                let paulis_reader: capnp::enum_list::Reader<'a, jeff_capnp::Pauli> = ppr
                    .get_pauli_string()
                    .expect("Pauli string should be present");
                GateOpType::PauliProdRotation {
                    pauli_string: PauliString::read_capnp(paulis_reader),
                }
            }
        };

        Ok(Self {
            gate_type,
            control_qubits,
            adjoint,
            power,
        })
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
}

impl<'a> PauliString<'a> {
    /// Create a new Pauli string from a capnp reader.
    pub(self) fn read_capnp(pauli_string: capnp::enum_list::Reader<'a, jeff_capnp::Pauli>) -> Self {
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
}

impl WellKnownGate {
    /// Create a new well-known gate type from a capnp reader.
    pub(self) fn read_capnp(well_known: jeff_capnp::WellKnownGate) -> Self {
        match well_known {
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
            #[allow(unreachable_patterns)]
            _ => unimplemented!(),
        }
    }
}
