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

fn check_uniform_int(
    inputs: &[Type],
    outputs: &[Type],
    name: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    for ty in inputs {
        if !matches!(ty, Type::Int { .. }) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !matches!(ty, Type::Int { .. }) {
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
        if !matches!(ty, Type::Float { .. }) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !matches!(ty, Type::Float { .. }) {
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
        IntOp::Const1(_) => {
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 1 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int const",
                });
            }
        }
        IntOp::Const8(_) => {
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 8 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int const",
                });
            }
        }
        IntOp::Const16(_) => {
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 16 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int const",
                });
            }
        }
        IntOp::Const32(_) => {
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int const",
                });
            }
        }
        IntOp::Const64(_) => {
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 64 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int const",
                });
            }
        }
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
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 1 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "int comparison",
                });
            }
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
            if outputs.first().is_some_and(|ty| {
                *ty != (Type::Float {
                    precision: FloatPrecision::Float32,
                })
            }) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "float const",
                });
            }
        }
        FloatOp::Const64(_) => {
            if outputs.first().is_some_and(|ty| {
                *ty != (Type::Float {
                    precision: FloatPrecision::Float64,
                })
            }) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "float const",
                });
            }
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
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 1 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "float predicate",
                });
            }
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
            if outputs.first().is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidOutputType { operation: "Alloc" });
            }
        }
        QubitOp::Free | QubitOp::FreeZero | QubitOp::Reset => {
            if inputs.first().is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qubit free/reset",
                });
            }
            if !outputs.is_empty() {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qubit free/reset",
                });
            }
        }
        QubitOp::Measure => {
            if inputs.first().is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "Measure",
                });
            }
            if outputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 1 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "Measure",
                });
            }
        }
        QubitOp::MeasureNd => {
            if inputs.first().is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "MeasureNd",
                });
            }
            if outputs.len() >= 2 {
                if outputs[0] != Type::Qubit {
                    errors.push(VerificationError::InvalidOutputType {
                        operation: "MeasureNd",
                    });
                }
                if outputs[1] != (Type::Int { bits: 1 }) {
                    errors.push(VerificationError::InvalidOutputType {
                        operation: "MeasureNd",
                    });
                }
            }
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
                    if *ty != Type::Qubit {
                        errors.push(VerificationError::InvalidInputType { operation: "Gate" });
                    }
                } else if i < num_qubits + num_params && !matches!(ty, Type::Float { .. }) {
                    errors.push(VerificationError::InvalidInputType { operation: "Gate" });
                }
            }
            for ty in outputs.iter().take(num_qubits) {
                if *ty != Type::Qubit {
                    errors.push(VerificationError::InvalidOutputType { operation: "Gate" });
                }
            }
        }
        _ => {}
    }
}

fn is_qureg(ty: &Type) -> bool {
    matches!(ty, Type::QubitRegister { .. })
}

fn check_qureg_op(
    qureg_op: QubitRegisterOp,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match qureg_op {
        QubitRegisterOp::Alloc => {
            if inputs
                .first()
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg alloc",
                });
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg alloc",
                });
            }
        }
        QubitRegisterOp::Free | QubitRegisterOp::FreeZero => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg free",
                });
            }
        }
        QubitRegisterOp::ExtractIndex => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg extractIndex",
                });
            }
            if inputs
                .get(1)
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg extractIndex",
                });
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg extractIndex",
                });
            }
            if outputs.get(1).is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg extractIndex",
                });
            }
        }
        QubitRegisterOp::InsertIndex => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertIndex",
                });
            }
            if inputs
                .get(1)
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertIndex",
                });
            }
            if inputs.get(2).is_some_and(|ty| *ty != Type::Qubit) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertIndex",
                });
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg insertIndex",
                });
            }
        }
        QubitRegisterOp::ExtractSlice => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg extractSlice",
                });
            }
            for ty in inputs.iter().skip(1).take(2) {
                if *ty != (Type::Int { bits: 32 }) {
                    errors.push(VerificationError::InvalidInputType {
                        operation: "qureg extractSlice",
                    });
                }
            }
            for ty in outputs.iter().take(2) {
                if !is_qureg(ty) {
                    errors.push(VerificationError::InvalidOutputType {
                        operation: "qureg extractSlice",
                    });
                }
            }
        }
        QubitRegisterOp::InsertSlice => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertSlice",
                });
            }
            if inputs
                .get(1)
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertSlice",
                });
            }
            if inputs.get(2).is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg insertSlice",
                });
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg insertSlice",
                });
            }
        }
        QubitRegisterOp::Length => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg length",
                });
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg length",
                });
            }
            if outputs
                .get(1)
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg length",
                });
            }
        }
        QubitRegisterOp::Split => {
            if inputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg split",
                });
            }
            if inputs
                .get(1)
                .is_some_and(|ty| *ty != (Type::Int { bits: 32 }))
            {
                errors.push(VerificationError::InvalidInputType {
                    operation: "qureg split",
                });
            }
            for ty in outputs.iter().take(2) {
                if !is_qureg(ty) {
                    errors.push(VerificationError::InvalidOutputType {
                        operation: "qureg split",
                    });
                }
            }
        }
        QubitRegisterOp::Join => {
            for ty in inputs.iter().take(2) {
                if !is_qureg(ty) {
                    errors.push(VerificationError::InvalidInputType {
                        operation: "qureg join",
                    });
                }
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg join",
                });
            }
        }
        QubitRegisterOp::Create => {
            for ty in inputs.iter() {
                if *ty != Type::Qubit {
                    errors.push(VerificationError::InvalidInputType {
                        operation: "qureg create",
                    });
                }
            }
            if outputs.first().is_some_and(|ty| !is_qureg(ty)) {
                errors.push(VerificationError::InvalidOutputType {
                    operation: "qureg create",
                });
            }
        }
        #[allow(unreachable_patterns)]
        _ => {}
    }
}
