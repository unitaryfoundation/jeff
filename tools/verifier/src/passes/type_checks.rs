//! Checks for correct input/output types and bitwidth/precision uniformity.

use jeff::reader::optype::{
    ControlFlowOp, FloatArrayOp, FloatOp, IntArrayOp, IntOp, OpType, QubitOp, QubitRegisterOp,
};
use jeff::reader::{Operation, Region};
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
            OpType::ControlFlowOp(cf_op) => check_cf_region_types(cf_op.as_ref(), op, errors),
            OpType::IntArrayOp(int_array_op) => {
                check_int_array_op(int_array_op, &inputs, &outputs, errors);
            }
            OpType::FloatArrayOp(float_array_op) => {
                check_float_array_op(float_array_op, &inputs, &outputs, errors);
            }
            // FuncOp only has a function index so type checking calls require to find the
            // callee signature at Module level, but this pass is only scoped to a Region.
            // TODO: Scope Module into this pass / add a helper pass to build a
            // function table for a signature lookup and check out of bounds index
            OpType::FuncOp(_) => {}
            _ => panic!("Unknown optype"),
        }
    }
}

fn check_cf_region_types(
    cf_op: &ControlFlowOp<'_>,
    op: Operation<'_>,
    errors: &mut Vec<VerificationError>,
) {
    match cf_op {
        ControlFlowOp::For { region } => {
            check_for_op(*region, op, errors);
        }
        ControlFlowOp::While { before, after } => {
            check_while_op(*before, *after, op, errors);
        }
        ControlFlowOp::Switch(switch_op) => {
            check_switch_op(switch_op, op, errors);
        }
    }
}

fn get_input_types(op: Operation<'_>) -> Vec<Type> {
    op.inputs().filter_map(|r| r.ok()).map(|v| v.ty()).collect()
}

fn get_output_types(op: Operation<'_>) -> Vec<Type> {
    op.outputs()
        .filter_map(|r| r.ok())
        .map(|v| v.ty())
        .collect()
}

fn get_source_types(region: Region<'_>) -> Vec<Type> {
    region
        .sources()
        .filter_map(|r| r.ok())
        .map(|v| v.ty())
        .collect()
}

fn get_target_types(region: Region<'_>) -> Vec<Type> {
    region
        .targets()
        .filter_map(|r| r.ok())
        .map(|v| v.ty())
        .collect()
}

fn check_for_op(region: Region<'_>, op: Operation<'_>, errors: &mut Vec<VerificationError>) {
    let input_types: Vec<Type> = get_input_types(op);
    let output_types: Vec<Type> = get_output_types(op);

    let region_source_types: Vec<Type> = get_source_types(region);
    let region_target_types: Vec<Type> = get_target_types(region);

    if !matches!(region_source_types.first(), Some(Type::Int { bits: 32 }))
        || region_source_types.get(1..) != input_types.get(3..)
        || region_source_types.get(1..) != Some(region_target_types.as_slice())
        || region_target_types != output_types
    {
        errors.push(VerificationError::RegionTypeMismatch { operation: "for" });
    }

    check_region_types(region, errors);
}

fn check_while_op(
    before: Region<'_>,
    after: Region<'_>,
    op: Operation<'_>,
    errors: &mut Vec<VerificationError>,
) {
    let input_types: Vec<Type> = get_input_types(op);
    let output_types: Vec<Type> = get_output_types(op);

    let before_source_types: Vec<Type> = get_source_types(before);
    let before_target_types: Vec<Type> = get_target_types(before);
    let after_source_types: Vec<Type> = get_source_types(after);
    let after_target_types: Vec<Type> = get_target_types(after);

    if before_source_types != input_types
        || before_source_types != after_target_types
        || !matches!(before_target_types.first(), Some(Type::Int { bits: 1 }))
        || before_target_types.get(1..) != Some(output_types.as_slice())
        || before_target_types.get(1..) != Some(after_source_types.as_slice())
    {
        errors.push(VerificationError::RegionTypeMismatch { operation: "while" });
    }

    check_region_types(before, errors);
    check_region_types(after, errors);
}

fn check_switch_op(
    switch_op: &jeff::reader::optype::SwitchOp<'_>,
    op: Operation<'_>,
    errors: &mut Vec<VerificationError>,
) {
    let input_types: Vec<Type> = get_input_types(op);
    let output_types: Vec<Type> = get_output_types(op);

    for branch in switch_op.branches() {
        let branch_source_types: Vec<Type> = get_source_types(branch);
        let branch_target_types: Vec<Type> = get_target_types(branch);

        if Some(branch_source_types.as_slice()) != input_types.get(1..)
            || branch_target_types != output_types
        {
            errors.push(VerificationError::RegionTypeMismatch {
                operation: "switch",
            });
        }

        check_region_types(branch, errors);
    }

    if let Some(default) = switch_op.default_branch() {
        let default_source_types: Vec<Type> = get_source_types(default);
        let default_target_types: Vec<Type> = get_target_types(default);

        if Some(default_source_types.as_slice()) != input_types.get(1..)
            || default_target_types != output_types
        {
            errors.push(VerificationError::RegionTypeMismatch {
                operation: "switch",
            });
        }

        check_region_types(default, errors);
    }
}

fn is_int(ty: &Type, bits: impl Into<Option<u8>>) -> bool {
    match bits.into() {
        Some(b) => matches!(ty, Type::Int { bits: x } if *x == b),
        None => matches!(ty, Type::Int { .. }),
    }
}

fn is_float(ty: &Type, precision: impl Into<Option<FloatPrecision>>) -> bool {
    match precision.into() {
        Some(p) => matches!(ty, Type::Float { precision: x } if *x == p),
        None => matches!(ty, Type::Float { .. }),
    }
}

fn is_qubit(ty: &Type) -> bool {
    matches!(ty, Type::Qubit)
}

fn is_qureg(ty: &Type) -> bool {
    matches!(ty, Type::QubitRegister { .. })
}

fn is_int_array(ty: &Type) -> bool {
    matches!(ty, Type::IntArray { .. })
}

fn is_float_array(ty: &Type) -> bool {
    matches!(ty, Type::FloatArray { .. })
}

fn expect_input(
    inputs: &[Type],
    idx: usize,
    pred: impl Fn(&Type) -> bool,
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
    pred: impl Fn(&Type) -> bool,
    op: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    if outputs.get(idx).is_some_and(|ty| !pred(ty)) {
        errors.push(VerificationError::InvalidOutputType { operation: op });
    }
}

fn check_arity(
    inputs: &[Type],
    expected_inputs: usize,
    outputs: &[Type],
    expected_outputs: usize,
    op: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    if inputs.len() != expected_inputs || outputs.len() != expected_outputs {
        errors.push(VerificationError::WrongArity { operation: op });
    }
}

fn check_uniform_int(
    inputs: &[Type],
    outputs: &[Type],
    name: &'static str,
    errors: &mut Vec<VerificationError>,
) {
    for ty in inputs {
        if !is_int(ty, None) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !is_int(ty, None) {
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
        if !is_float(ty, None) {
            errors.push(VerificationError::InvalidInputType { operation: name });
            return;
        }
    }
    for ty in outputs {
        if !is_float(ty, None) {
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
            check_arity(inputs, 0, outputs, 1, "int const", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 1), "int const", errors);
        }
        IntOp::Const8(_) => {
            check_arity(inputs, 0, outputs, 1, "int const", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 8), "int const", errors);
        }
        IntOp::Const16(_) => {
            check_arity(inputs, 0, outputs, 1, "int const", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 16), "int const", errors);
        }
        IntOp::Const32(_) => {
            check_arity(inputs, 0, outputs, 1, "int const", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 32), "int const", errors);
        }
        IntOp::Const64(_) => {
            check_arity(inputs, 0, outputs, 1, "int const", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 64), "int const", errors);
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
        | IntOp::Shr => {
            check_arity(inputs, 2, outputs, 1, "int arithmetic", errors);
            check_uniform_int(inputs, outputs, "int arithmetic", errors);
        }
        IntOp::Not | IntOp::Abs => {
            check_arity(inputs, 1, outputs, 1, "int arithmetic", errors);
            check_uniform_int(inputs, outputs, "int arithmetic", errors);
        }
        IntOp::Eq | IntOp::LtS | IntOp::LteS | IntOp::LtU | IntOp::LteU => {
            check_arity(inputs, 2, outputs, 1, "int comparison", errors);
            check_uniform_int(inputs, &[], "int comparison", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 1), "int comparison", errors);
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
            check_arity(inputs, 0, outputs, 1, "float const", errors);
            expect_output(
                outputs,
                0,
                |ty| is_float(ty, FloatPrecision::Float32),
                "float const",
                errors,
            );
        }
        FloatOp::Const64(_) => {
            check_arity(inputs, 0, outputs, 1, "float const", errors);
            expect_output(
                outputs,
                0,
                |ty| is_float(ty, FloatPrecision::Float64),
                "float const",
                errors,
            );
        }
        FloatOp::Add
        | FloatOp::Sub
        | FloatOp::Mul
        | FloatOp::Pow
        | FloatOp::Atan2
        | FloatOp::Max
        | FloatOp::Min => {
            check_arity(inputs, 2, outputs, 1, "float op", errors);
            check_uniform_float(inputs, outputs, "float op", errors);
        }
        FloatOp::Sqrt
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
            check_arity(inputs, 1, outputs, 1, "float op", errors);
            check_uniform_float(inputs, outputs, "float op", errors);
        }
        FloatOp::Eq | FloatOp::Lt | FloatOp::Lte => {
            check_arity(inputs, 2, outputs, 1, "float predicate", errors);
            check_uniform_float(inputs, &[], "float predicate", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 1), "float predicate", errors);
        }
        FloatOp::IsNan | FloatOp::IsInf => {
            check_arity(inputs, 1, outputs, 1, "float predicate", errors);
            check_uniform_float(inputs, &[], "float predicate", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 1), "float predicate", errors);
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
            check_arity(inputs, 0, outputs, 1, "Alloc", errors);
            expect_output(outputs, 0, is_qubit, "Alloc", errors);
        }
        QubitOp::Free | QubitOp::FreeZero => {
            check_arity(inputs, 1, outputs, 0, "qubit free", errors);
            expect_input(inputs, 0, is_qubit, "qubit free", errors);
        }
        QubitOp::Reset => {
            check_arity(inputs, 1, outputs, 1, "Reset", errors);
            expect_input(inputs, 0, is_qubit, "Reset", errors);
            expect_output(outputs, 0, is_qubit, "Reset", errors);
        }
        QubitOp::Measure => {
            check_arity(inputs, 1, outputs, 1, "Measure", errors);
            expect_input(inputs, 0, is_qubit, "Measure", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 1), "Measure", errors);
        }
        QubitOp::MeasureNd => {
            check_arity(inputs, 1, outputs, 2, "MeasureNd", errors);
            expect_input(inputs, 0, is_qubit, "MeasureNd", errors);
            expect_output(outputs, 0, is_qubit, "MeasureNd", errors);
            expect_output(outputs, 1, |ty| is_int(ty, 1), "MeasureNd", errors);
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
                } else if i < num_qubits + num_params && !is_float(ty, None) {
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
            check_arity(inputs, 1, outputs, 1, "qureg alloc", errors);
            expect_input(inputs, 0, |ty| is_int(ty, 32), "qureg alloc", errors);
            expect_output(outputs, 0, is_qureg, "qureg alloc", errors);
        }
        QubitRegisterOp::Free | QubitRegisterOp::FreeZero => {
            check_arity(inputs, 1, outputs, 0, "qureg free", errors);
            expect_input(inputs, 0, is_qureg, "qureg free", errors);
        }
        QubitRegisterOp::ExtractIndex => {
            check_arity(inputs, 2, outputs, 2, "qureg extractIndex", errors);
            expect_input(inputs, 0, is_qureg, "qureg extractIndex", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "qureg extractIndex", errors);
            expect_output(outputs, 0, is_qureg, "qureg extractIndex", errors);
            expect_output(outputs, 1, is_qubit, "qureg extractIndex", errors);
        }
        QubitRegisterOp::InsertIndex => {
            check_arity(inputs, 3, outputs, 1, "qureg insertIndex", errors);
            expect_input(inputs, 0, is_qureg, "qureg insertIndex", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "qureg insertIndex", errors);
            expect_input(inputs, 2, is_qubit, "qureg insertIndex", errors);
            expect_output(outputs, 0, is_qureg, "qureg insertIndex", errors);
        }
        QubitRegisterOp::ExtractSlice => {
            check_arity(inputs, 3, outputs, 2, "qureg extractSlice", errors);
            expect_input(inputs, 0, is_qureg, "qureg extractSlice", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "qureg extractSlice", errors);
            expect_input(inputs, 2, |ty| is_int(ty, 32), "qureg extractSlice", errors);
            expect_output(outputs, 0, is_qureg, "qureg extractSlice", errors);
            expect_output(outputs, 1, is_qureg, "qureg extractSlice", errors);
        }
        QubitRegisterOp::InsertSlice => {
            check_arity(inputs, 3, outputs, 1, "qureg insertSlice", errors);
            expect_input(inputs, 0, is_qureg, "qureg insertSlice", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "qureg insertSlice", errors);
            expect_input(inputs, 2, is_qureg, "qureg insertSlice", errors);
            expect_output(outputs, 0, is_qureg, "qureg insertSlice", errors);
        }
        QubitRegisterOp::Length => {
            check_arity(inputs, 1, outputs, 2, "qureg length", errors);
            expect_input(inputs, 0, is_qureg, "qureg length", errors);
            expect_output(outputs, 0, is_qureg, "qureg length", errors);
            expect_output(outputs, 1, |ty| is_int(ty, 32), "qureg length", errors);
        }
        QubitRegisterOp::Split => {
            check_arity(inputs, 2, outputs, 2, "qureg split", errors);
            expect_input(inputs, 0, is_qureg, "qureg split", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "qureg split", errors);
            expect_output(outputs, 0, is_qureg, "qureg split", errors);
            expect_output(outputs, 1, is_qureg, "qureg split", errors);
        }
        QubitRegisterOp::Join => {
            check_arity(inputs, 2, outputs, 1, "qureg join", errors);
            expect_input(inputs, 0, is_qureg, "qureg join", errors);
            expect_input(inputs, 1, is_qureg, "qureg join", errors);
            expect_output(outputs, 0, is_qureg, "qureg join", errors);
        }
        QubitRegisterOp::Create => {
            if outputs.len() != 1 {
                errors.push(VerificationError::WrongArity {
                    operation: "qureg create",
                });
            }
            for ty in inputs.iter() {
                if !is_qubit(ty) {
                    errors.push(VerificationError::InvalidInputType {
                        operation: "qureg create",
                    });
                }
            }
            expect_output(outputs, 0, is_qureg, "qureg create", errors);
        }
        _ => {}
    }
}

fn check_int_array_op(
    int_array_op: IntArrayOp<'_>,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match int_array_op {
        IntArrayOp::ConstArray1(_) => {
            check_arity(inputs, 0, outputs, 1, "int array const", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: 1, .. }),
                "int array const",
                errors,
            );
        }
        IntArrayOp::ConstArray8(_) => {
            check_arity(inputs, 0, outputs, 1, "int array const", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: 8, .. }),
                "int array const",
                errors,
            );
        }
        IntArrayOp::ConstArray16(_) => {
            check_arity(inputs, 0, outputs, 1, "int array const", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: 16, .. }),
                "int array const",
                errors,
            );
        }
        IntArrayOp::ConstArray32(_) => {
            check_arity(inputs, 0, outputs, 1, "int array const", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: 32, .. }),
                "int array const",
                errors,
            );
        }
        IntArrayOp::ConstArray64(_) => {
            check_arity(inputs, 0, outputs, 1, "int array const", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: 64, .. }),
                "int array const",
                errors,
            );
        }
        IntArrayOp::Zero { bits } => {
            check_arity(inputs, 1, outputs, 1, "int array zero", errors);
            expect_input(inputs, 0, |ty| is_int(ty, 32), "int array zero", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::IntArray { bits: b, .. } if *b == bits),
                "int array zero",
                errors,
            );
        }
        IntArrayOp::GetIndex => {
            check_arity(inputs, 2, outputs, 1, "int array getIndex", errors);
            expect_input(inputs, 0, is_int_array, "int array getIndex", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "int array getIndex", errors);
            if let (Some(Type::IntArray { bits, .. }), Some(out_ty)) =
                (inputs.first(), outputs.first())
            {
                if !is_int(out_ty, *bits) {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "int array getIndex",
                    });
                }
            }
        }
        IntArrayOp::SetIndex => {
            check_arity(inputs, 3, outputs, 1, "int array setIndex", errors);
            expect_input(inputs, 0, is_int_array, "int array setIndex", errors);
            expect_input(inputs, 1, |ty| is_int(ty, 32), "int array setIndex", errors);
            if let Some(Type::IntArray { bits, .. }) = inputs.first() {
                let bits = *bits;
                if inputs.get(2).is_some_and(|ty| !is_int(ty, bits)) {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "int array setIndex",
                    });
                }
                if outputs
                    .first()
                    .is_some_and(|ty| !matches!(ty, Type::IntArray { bits: b, .. } if *b == bits))
                {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "int array setIndex",
                    });
                }
            }
        }
        IntArrayOp::Length => {
            check_arity(inputs, 1, outputs, 1, "int array length", errors);
            expect_input(inputs, 0, is_int_array, "int array length", errors);
            expect_output(outputs, 0, |ty| is_int(ty, 32), "int array length", errors);
        }
        IntArrayOp::Create => {
            if outputs.len() != 1 {
                errors.push(VerificationError::WrongArity {
                    operation: "int array create",
                });
            }
            expect_output(outputs, 0, is_int_array, "int array create", errors);
            if let Some(Type::IntArray { bits, .. }) = outputs.first() {
                let bits = *bits;
                for ty in inputs.iter() {
                    if !is_int(ty, bits) {
                        errors.push(VerificationError::TypeMismatch {
                            operation: "int array create",
                        });
                        break;
                    }
                }
            }
        }
        _ => {}
    }
}

fn check_float_array_op(
    float_array_op: FloatArrayOp<'_>,
    inputs: &[Type],
    outputs: &[Type],
    errors: &mut Vec<VerificationError>,
) {
    match float_array_op {
        FloatArrayOp::Const32(_) => {
            check_arity(inputs, 0, outputs, 1, "float array const", errors);
            expect_output(
                outputs,
                0,
                |ty| {
                    matches!(
                        ty,
                        Type::FloatArray {
                            precision: FloatPrecision::Float32,
                            ..
                        }
                    )
                },
                "float array const",
                errors,
            );
        }
        FloatArrayOp::Const64(_) => {
            check_arity(inputs, 0, outputs, 1, "float array const", errors);
            expect_output(
                outputs,
                0,
                |ty| {
                    matches!(
                        ty,
                        Type::FloatArray {
                            precision: FloatPrecision::Float64,
                            ..
                        }
                    )
                },
                "float array const",
                errors,
            );
        }
        FloatArrayOp::Zero { precision } => {
            check_arity(inputs, 1, outputs, 1, "float array zero", errors);
            expect_input(inputs, 0, |ty| is_int(ty, 32), "float array zero", errors);
            expect_output(
                outputs,
                0,
                |ty| matches!(ty, Type::FloatArray { precision: p, .. } if *p == precision),
                "float array zero",
                errors,
            );
        }
        FloatArrayOp::GetIndex => {
            check_arity(inputs, 2, outputs, 1, "float array getIndex", errors);
            expect_input(inputs, 0, is_float_array, "float array getIndex", errors);
            expect_input(
                inputs,
                1,
                |ty| is_int(ty, 32),
                "float array getIndex",
                errors,
            );
            if let (Some(Type::FloatArray { precision, .. }), Some(out_ty)) =
                (inputs.first(), outputs.first())
            {
                if !is_float(out_ty, *precision) {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "float array getIndex",
                    });
                }
            }
        }
        FloatArrayOp::SetIndex => {
            check_arity(inputs, 3, outputs, 1, "float array setIndex", errors);
            expect_input(inputs, 0, is_float_array, "float array setIndex", errors);
            expect_input(
                inputs,
                1,
                |ty| is_int(ty, 32),
                "float array setIndex",
                errors,
            );
            if let Some(Type::FloatArray { precision, .. }) = inputs.first() {
                let precision = *precision;
                if inputs.get(2).is_some_and(|ty| !is_float(ty, precision)) {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "float array setIndex",
                    });
                }
                if outputs.first().is_some_and(
                    |ty| !matches!(ty, Type::FloatArray { precision: p, .. } if *p == precision),
                ) {
                    errors.push(VerificationError::TypeMismatch {
                        operation: "float array setIndex",
                    });
                }
            }
        }
        FloatArrayOp::Length => {
            check_arity(inputs, 1, outputs, 1, "float array length", errors);
            expect_input(inputs, 0, is_float_array, "float array length", errors);
            expect_output(
                outputs,
                0,
                |ty| is_int(ty, 32),
                "float array length",
                errors,
            );
        }
        FloatArrayOp::Create => {
            if outputs.len() != 1 {
                errors.push(VerificationError::WrongArity {
                    operation: "float array create",
                });
            }
            expect_output(outputs, 0, is_float_array, "float array create", errors);
            if let Some(Type::FloatArray { precision, .. }) = outputs.first() {
                let precision = *precision;
                for ty in inputs.iter() {
                    if !is_float(ty, precision) {
                        errors.push(VerificationError::TypeMismatch {
                            operation: "float array create",
                        });
                        break;
                    }
                }
            }
        }
        _ => {}
    }
}
