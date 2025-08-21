//! Node operation definitions.

mod const_val;
mod control_flow;
mod float;
mod int;
pub mod qubit;

pub use const_val::ConstArray;
pub use control_flow::{ControlFlowOp, FuncOp, SwitchOp};
pub use float::{FloatArrayOp, FloatOp};
pub use int::{IntArrayOp, IntOp};
pub use qubit::{GateOp, GateOpType, QubitOp, QubitRegisterOp, WellKnownGate};

use crate::jeff_capnp;
use crate::reader::value::ValueTable;

use super::string_table::StringTable;

/// The type of an operation.
#[derive(Clone, Debug)]
#[non_exhaustive]
/// Represents different types of operations.
pub enum OpType<'a> {
    /// Operation on a single qubit.
    QubitOp(QubitOp<'a>),
    /// Operation on a register of qubits.
    QubitRegisterOp(QubitRegisterOp),
    /// Operation involving an integer.
    IntOp(IntOp),
    /// Operation involving an array of integers.
    IntArrayOp(IntArrayOp<'a>),
    /// Operation involving a floating-point number.
    FloatOp(FloatOp),
    /// Operation involving an array of floating-point numbers.
    FloatArrayOp(FloatArrayOp<'a>),
    /// Operation for control flow.
    //
    // Wrapped in a Box to reduce the size of the enum.
    ControlFlowOp(Box<ControlFlowOp<'a>>),
    /// Operation involving a function.
    FuncOp(FuncOp),
}

impl<'a> OpType<'a> {
    /// Create a new operation type from a capnp reader.
    pub(crate) fn read_capnp(
        op: jeff_capnp::op::instruction::Reader<'a>,
        strings: StringTable<'a>,
        values: ValueTable<'a>,
    ) -> Self {
        match op.which() {
            Ok(jeff_capnp::op::instruction::Which::Qubit(qubit_op)) => OpType::QubitOp(
                QubitOp::read_capnp(qubit_op.expect("Qubit op should be valid"), strings),
            ),
            Ok(jeff_capnp::op::instruction::Which::Qureg(qubit_reg_op)) => {
                OpType::QubitRegisterOp(QubitRegisterOp::read_capnp(
                    qubit_reg_op.expect("Qubit register op should be valid"),
                ))
            }
            Ok(jeff_capnp::op::instruction::Which::Int(int_op)) => {
                OpType::IntOp(IntOp::read_capnp(int_op.expect("Int op should be valid")))
            }
            Ok(jeff_capnp::op::instruction::Which::IntArray(int_array_op)) => OpType::IntArrayOp(
                IntArrayOp::read_capnp(int_array_op.expect("Int array op should be valid")),
            ),
            Ok(jeff_capnp::op::instruction::Which::Float(float_op)) => OpType::FloatOp(
                FloatOp::read_capnp(float_op.expect("Float op should be valid")),
            ),
            Ok(jeff_capnp::op::instruction::Which::FloatArray(float_array_op)) => {
                OpType::FloatArrayOp(FloatArrayOp::read_capnp(
                    float_array_op.expect("Float array op should be valid"),
                ))
            }
            Ok(jeff_capnp::op::instruction::Which::Scf(control_flow_op)) => {
                OpType::ControlFlowOp(Box::new(ControlFlowOp::read_capnp(
                    control_flow_op.expect("Control flow op should be valid"),
                    strings,
                    values,
                )))
            }
            Ok(jeff_capnp::op::instruction::Which::Func(func_op)) => OpType::FuncOp(FuncOp {
                func_idx: func_op.expect("Function should be valid").get_func_call(),
            }),
            Err(_) => panic!("Invalid operation type"),
        }
    }
}
