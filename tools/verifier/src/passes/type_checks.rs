//! Checks for correct input/output types and bitwidth/precision uniformity.

use jeff::reader::optype::{ControlFlowOp, FloatOp, IntOp, OpType, QubitOp, QubitRegisterOp};
use jeff::reader::Region;
use jeff::types::{FloatPrecision, Type};

use crate::VerificationError;

/// Check that all operations in `region` (and its nested regions) have correctly typed inputs and outputs.
pub fn verify_operation_types(region: Region<'_>, errors: &mut Vec<VerificationError>) {
    check_region_types(region, errors);
}

fn check_region_types(region: Region<'_>, errors: &mut Vec<VerificationError>) {
    for op in region.operations() {
        let inputs: Vec<Type> = op.inputs().filter_map(|r| r.ok()).map(|v| v.ty()).collect();
        let outputs: Vec<Type> = op
            .outputs()
            .filter_map(|r| r.ok())
            .map(|v| v.ty())
            .collect();

        match op.op_type() {
            OpType::IntOp(int_op) => check_int_op(int_op, &inputs, &outputs, errors),
            OpType::FloatOp(float_op) => check_float_op(float_op, &inputs, &outputs, errors),
            OpType::QubitOp(qubit_op) => check_qubit_op(qubit_op, &inputs, &outputs, errors),
            OpType::QubitRegisterOp(qureg_op) => {
                check_qureg_op(qureg_op, &inputs, &outputs, errors);
            }
            OpType::ControlFlowOp(cf_op) => check_cf_region_types(cf_op.as_ref(), errors),
            _ => {}
        }
    }
}

fn check_cf_region_types(cf_op: &ControlFlowOp<'_>, errors: &mut Vec<VerificationError>) {
    match cf_op {
        ControlFlowOp::For { region } => check_region_types(*region, errors),
        ControlFlowOp::While { condition, body } => {
            check_region_types(*condition, errors);
            check_region_types(*body, errors);
        }
        ControlFlowOp::DoWhile { body, condition } => {
            check_region_types(*body, errors);
            check_region_types(*condition, errors);
        }
        ControlFlowOp::Switch(switch_op) => {
            for branch in switch_op.branches() {
                check_region_types(branch, errors);
            }
            if let Some(default) = switch_op.default_branch() {
                check_region_types(default, errors);
            }
        }
    }
}

fn is_int(ty: &Type) -> bool {
    matches!(ty, Type::Int { .. })
}

fn is_float(ty: &Type) -> bool {
    matches!(ty, Type::Float { .. })
}

fn is_qubit(ty: &Type) -> bool {
    *ty == Type::Qubit
}

fn is_qureg(ty: &Type) -> bool {
    matches!(ty, Type::QubitRegister { .. })
}

fn is_i1(ty: &Type) -> bool {
    *ty == (Type::Int { bits: 1 })
}

fn is_i32(ty: &Type) -> bool {
    *ty == (Type::Int { bits: 32 })
}

fn expect_input(
    inputs: &[Type],
    idx: usize,
    pred: fn(&Type) -> bool,
    op: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    if inputs.get(idx).is_some_and(|ty| !pred(ty)) {
        errors.push(VerificationError::InvalidInputType { operation: op });
    }
}

fn expect_output(
    outputs: &[Type],
    idx: usize,
    pred: fn(&Type) -> bool,
    op: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    if outputs.get(idx).is_some_and(|ty| !pred(ty)) {
        errors.push(VerificationError::InvalidOutputType { operation: op });
    }
}

fn check_const_int_output(outputs: &[Type], bits: u8, errors: &mut Vec<VerificationError>) {
    if outputs
        .first()
        .is_some_and(|ty| *ty != (Type::Int { bits }))
    {
        errors.push(VerificationError::InvalidOutputType {
            operation: "int const",
        });
    }
}

fn check_const_float_output(
    outputs: &[Type],
    precision: FloatPrecision,
    errors: &mut Vec<VerificationError>,
) {
    if outputs
        .first()
        .is_some_and(|ty| *ty != (Type::Float { precision }))
    {
        errors.push(VerificationError::InvalidOutputType {
            operation: "float const",
        });
    }
}

fn check_uniform_int(
    inputs: &[Type],
    outputs: &[Type],
    name: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    for ty in inputs {
        if !is_int(ty) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !is_int(ty) {
            errors.push(VerificationError::InvalidOutputType { operation: name });
            return;
        }
    }
    let mut bits: Option<u8> = None;
    for ty in inputs.iter().chain(outputs.iter()) {
        if let Type::Int { bits: b } = ty {
            match bits {
                None => bits = Some(*b),
                Some(existing) if existing != *b => {
                    errors.push(VerificationError::TypeMismatch { operation: name });
                    return;
                }
                _ => {}
            }
        }
    }
}

fn check_uniform_float(
    inputs: &[Type],
    outputs: &[Type],
    name: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    for ty in inputs {
        if !is_float(ty) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !is_float(ty) {
            errors.push(VerificationError::InvalidOutputType { operation: name });
            return;
        }
    }
    let mut precision: Option<FloatPrecision> = None;
    for ty in inputs.iter().chain(outputs.iter()) {
        if let Type::Float { precision: p } = ty {
            match precision {
                None => precision = Some(*p),
                Some(existing) if existing != *p => {
                    errors.push(VerificationError::TypeMismatch { operation: name });
                    return;
                }
                _ => {}
            }
        }
    }
}

fn check_int_op(
    int_op: IntOp,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match int_op {
        IntOp::Const1(_) => check_const_int_output(outputs, 1, errors),
        IntOp::Const8(_) => check_const_int_output(outputs, 8, errors),
        IntOp::Const16(_) => check_const_int_output(outputs, 16, errors),
        IntOp::Const32(_) => check_const_int_output(outputs, 32, errors),
        IntOp::Const64(_) => check_const_int_output(outputs, 64, errors),
        IntOp::Add
        | IntOp::Sub
        | IntOp::Mul
        | IntOp::DivS
        | IntOp::DivU
        | IntOp::Pow
        | IntOp::And
        | IntOp::Or
        | IntOp::Xor
        | IntOp::MinS
        | IntOp::MinU
        | IntOp::MaxS
        | IntOp::MaxU
        | IntOp::RemS
        | IntOp::RemU
        | IntOp::Shl
        | IntOp::Shr
        | IntOp::Not
        | IntOp::Abs => {
            check_uniform_int(inputs, outputs, "int arithmetic", errors);
        }
        IntOp::Eq | IntOp::LtS | IntOp::LteS | IntOp::LtU | IntOp::LteU => {
            check_uniform_int(inputs, &[], "int comparison", errors);
            expect_output(outputs, 0, is_i1, "int comparison", errors);
        }
        _ => {}
    }
}

fn check_float_op(
    float_op: FloatOp,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match float_op {
        FloatOp::Const32(_) => {
            check_const_float_output(outputs, FloatPrecision::Float32, errors);
        }
        FloatOp::Const64(_) => {
            check_const_float_output(outputs, FloatPrecision::Float64, errors);
        }
        FloatOp::Add
        | FloatOp::Sub
        | FloatOp::Mul
        | FloatOp::Pow
        | FloatOp::Max
        | FloatOp::Min
        | FloatOp::Atan2
        | FloatOp::Sqrt
        | FloatOp::Abs
        | FloatOp::Ceil
        | FloatOp::Floor
        | FloatOp::Exp
        | FloatOp::Log
        | FloatOp::Sin
        | FloatOp::Cos
        | FloatOp::Tan
        | FloatOp::Asin
        | FloatOp::Acos
        | FloatOp::Atan
        | FloatOp::Sinh
        | FloatOp::Cosh
        | FloatOp::Tanh
        | FloatOp::Asinh
        | FloatOp::Acosh
        | FloatOp::Atanh => {
            check_uniform_float(inputs, outputs, "float op", errors);
        }
        FloatOp::Eq | FloatOp::Lt | FloatOp::Lte | FloatOp::IsNan | FloatOp::IsInf => {
            check_uniform_float(inputs, &[], "float predicate", errors);
            expect_output(outputs, 0, is_i1, "float predicate", errors);
        }
        _ => {}
    }
}

fn check_qubit_op(
    qubit_op: QubitOp<'_>,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match qubit_op {
        QubitOp::Alloc => {
            if !inputs.is_empty() {
                errors.push(VerificationError::InvalidInputType { operation: "Alloc" });
            }
            expect_output(outputs, 0, is_qubit, "Alloc", errors);
        }
        QubitOp::Free | QubitOp::FreeZero | QubitOp::Reset => {
            expect_input(inputs, 0, is_qubit, "qubit free/reset", errors);
            if !outputs.is_empty() {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qubit free/reset",
                });
            }
        }
        QubitOp::Measure => {
            expect_input(inputs, 0, is_qubit, "Measure", errors);
            expect_output(outputs, 0, is_i1, "Measure", errors);
        }
        QubitOp::MeasureNd => {
            expect_input(inputs, 0, is_qubit, "MeasureNd", errors);
            expect_output(outputs, 0, is_qubit, "MeasureNd", errors);
            expect_output(outputs, 1, is_i1, "MeasureNd", errors);
        }
        QubitOp::Gate(gate) => {
            let num_qubits = gate.num_qubits();
            let num_params = gate.num_params();
            if inputs.len() != num_qubits + num_params {
                errors.push(VerificationError::WrongArity { operation: "Gate" });
            }
            if outputs.len() != num_qubits {
                errors.push(VerificationError::WrongArity { operation: "Gate" });
            }
            for (i, ty) in inputs.iter().enumerate() {
                if i < num_qubits {
                    if !is_qubit(ty) {
                        errors.push(VerificationError::InvalidInputType { operation: "Gate" });
                    }
                } else if i < num_qubits + num_params && !is_float(ty) {
                    errors.push(VerificationError::InvalidInputType { operation: "Gate" });
                }
            }
            for ty in outputs.iter().take(num_qubits) {
                if !is_qubit(ty) {
                    errors.push(VerificationError::InvalidOutputType { operation: "Gate" });
                }
            }
        }
        _ => {}
    }
}

fn check_qureg_op(
    qureg_op: QubitRegisterOp,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match qureg_op {
        QubitRegisterOp::Alloc => {
            expect_input(inputs, 0, is_i32, "qureg alloc", errors);
            expect_output(outputs, 0, is_qureg, "qureg alloc", errors);
        }
        QubitRegisterOp::Free | QubitRegisterOp::FreeZero => {
            expect_input(inputs, 0, is_qureg, "qureg free", errors);
        }
        QubitRegisterOp::ExtractIndex => {
            expect_input(inputs, 0, is_qureg, "qureg extractIndex", errors);
            expect_input(inputs, 1, is_i32, "qureg extractIndex", errors);
            expect_output(outputs, 0, is_qureg, "qureg extractIndex", errors);
            expect_output(outputs, 1, is_qubit, "qureg extractIndex", errors);
        }
        QubitRegisterOp::InsertIndex => {
            expect_input(inputs, 0, is_qureg, "qureg insertIndex", errors);
            expect_input(inputs, 1, is_i32, "qureg insertIndex", errors);
            expect_input(inputs, 2, is_qubit, "qureg insertIndex", errors);
            expect_output(outputs, 0, is_qureg, "qureg insertIndex", errors);
        }
        QubitRegisterOp::ExtractSlice => {
            expect_input(inputs, 0, is_qureg, "qureg extractSlice", errors);
            expect_input(inputs, 1, is_i32, "qureg extractSlice", errors);
            expect_input(inputs, 2, is_i32, "qureg extractSlice", errors);
            expect_output(outputs, 0, is_qureg, "qureg extractSlice", errors);
            expect_output(outputs, 1, is_qureg, "qureg extractSlice", errors);
        }
        QubitRegisterOp::InsertSlice => {
            expect_input(inputs, 0, is_qureg, "qureg insertSlice", errors);
            expect_input(inputs, 1, is_i32, "qureg insertSlice", errors);
            expect_input(inputs, 2, is_qureg, "qureg insertSlice", errors);
            expect_output(outputs, 0, is_qureg, "qureg insertSlice", errors);
        }
        QubitRegisterOp::Length => {
            expect_input(inputs, 0, is_qureg, "qureg length", errors);
            expect_output(outputs, 0, is_qureg, "qureg length", errors);
            expect_output(outputs, 1, is_i32, "qureg length", errors);
        }
        QubitRegisterOp::Split => {
            expect_input(inputs, 0, is_qureg, "qureg split", errors);
            expect_input(inputs, 1, is_i32, "qureg split", errors);
            expect_output(outputs, 0, is_qureg, "qureg split", errors);
            expect_output(outputs, 1, is_qureg, "qureg split", errors);
        }
        QubitRegisterOp::Join => {
            expect_input(inputs, 0, is_qureg, "qureg join", errors);
            expect_input(inputs, 1, is_qureg, "qureg join", errors);
            expect_output(outputs, 0, is_qureg, "qureg join", errors);
        }
        QubitRegisterOp::Create => {
            for ty in inputs.iter() {
                if !is_qubit(ty) {
                    errors.push(VerificationError::InvalidInputType {
                        operation: "qureg create",
                    });
                }
            }
            expect_output(outputs, 0, is_qureg, "qureg create", errors);
        }
        #[allow(unreachable_patterns)]
        _ => {}
    }
}
