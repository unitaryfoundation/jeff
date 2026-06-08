use jeff::reader::optype::{
    ControlFlowOp, FloatOp, FuncOp, IntArrayOp, IntOp, OpType, QubitOp, QubitRegisterOp,
};
use jeff::reader::Module;
use jeff::types::{FloatPrecision, Type};

use super::{Check, CheckError};

pub struct TypesCheck;

impl Check for TypesCheck {
    fn name(&self) -> &'static str {
        "types"
    }

    fn check(&self, module: &Module<'_>) -> Vec<CheckError> {
        let mut errors = vec![];

        for func in module.functions() {
            let func_name = func.name().to_string();
            let definition = match func {
                jeff::reader::Function::Definition(def) => def,
                jeff::reader::Function::Declaration(_) => continue,
            };

            let body = definition.body();
            for (op_idx, op) in body.operations().enumerate() {
                let op_type = op.op_type();
                let op_errors = check_op_types(&func_name, op_idx, &op_type, &op);
                errors.extend(op_errors);
            }
        }

        errors
    }
}

fn check_op_types(
    func_name: &str,
    op_idx: usize,
    op_type: &OpType<'_>,
    op: &jeff::reader::Operation<'_>,
) -> Vec<CheckError> {
    let mut errors = vec![];
    match op_type {
        OpType::QubitOp(qubit_op) => check_qubit_op(func_name, op_idx, qubit_op, op, &mut errors),
        OpType::QubitRegisterOp(qreg_op) => {
            check_qureg_op(func_name, op_idx, qreg_op, op, &mut errors)
        }
        OpType::IntOp(int_op) => check_int_op(func_name, op_idx, int_op, op, &mut errors),
        OpType::IntArrayOp(int_arr_op) => {
            check_int_array_op(func_name, op_idx, int_arr_op, op, &mut errors)
        }
        OpType::FloatOp(float_op) => check_float_op(func_name, op_idx, float_op, op, &mut errors),
        OpType::FloatArrayOp(float_arr_op) => {
            check_float_array_op(func_name, op_idx, float_arr_op, op, &mut errors);
        }
        OpType::ControlFlowOp(cf_op) => {
            check_control_flow_op(func_name, op_idx, cf_op, op, &mut errors)
        }
        OpType::FuncOp(func_op) => check_func_op(func_name, op_idx, func_op, op, &mut errors),
        _ => {}
    }
    errors
}

fn collect_types(
    op: &jeff::reader::Operation<'_>,
    dir: jeff::Direction,
) -> Vec<(usize, u32, Type)> {
    let mut types = vec![];
    let iter: Box<
        dyn Iterator<Item = Result<jeff::reader::value::WireValue<'_>, jeff::reader::ReadError>>,
    > = match dir {
        jeff::Direction::Incoming => Box::new(op.inputs()),
        jeff::Direction::Outgoing => Box::new(op.outputs()),
    };
    for (i, result) in iter.enumerate() {
        if let Ok(v) = result {
            types.push((i, v.id(), v.ty()));
        }
    }
    types
}

fn check_qubit_op(
    func_name: &str,
    op_idx: usize,
    qubit_op: &QubitOp<'_>,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    let op_tag = "QubitOp";

    match qubit_op {
        QubitOp::Alloc => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(func_name, op_idx, op_tag, &outputs, 0, &Type::Qubit, errors);
        }
        QubitOp::Free | QubitOp::FreeZero => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 0, &outputs, errors);
            expect_type(func_name, op_idx, op_tag, &inputs, 0, &Type::Qubit, errors);
        }
        QubitOp::Measure | QubitOp::MeasureNd => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_type(func_name, op_idx, op_tag, &inputs, 0, &Type::Qubit, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(1),
                errors,
            );
        }
        QubitOp::Reset => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(func_name, op_idx, op_tag, &inputs, 0, &Type::Qubit, errors);
            expect_type(func_name, op_idx, op_tag, &outputs, 0, &Type::Qubit, errors);
        }
        QubitOp::Gate(gate_op) => {
            let num_qubits = gate_op.num_qubits();
            let num_params = gate_op.num_params();
            let total_qubit_inputs = num_qubits;
            let total_inputs = total_qubit_inputs + num_params;
            let total_outputs = num_qubits;
            expect_count(func_name, op_idx, op_tag, total_inputs, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, total_outputs, &outputs, errors);
            for i in 0..total_qubit_inputs {
                expect_type(func_name, op_idx, op_tag, &inputs, i, &Type::Qubit, errors);
            }
            for i in 0..total_outputs {
                expect_type(func_name, op_idx, op_tag, &outputs, i, &Type::Qubit, errors);
            }
            for i in total_qubit_inputs..total_inputs {
                expect_type(
                    func_name,
                    op_idx,
                    op_tag,
                    &inputs,
                    i,
                    &Type::Float {
                        precision: FloatPrecision::Float64,
                    },
                    errors,
                );
            }
        }
        _ => {}
    }
}

fn qureg_op_name(qreg_op: &QubitRegisterOp) -> &'static str {
    match qreg_op {
        QubitRegisterOp::Alloc => "QubitRegisterOp::Alloc",
        QubitRegisterOp::Free => "QubitRegisterOp::Free",
        QubitRegisterOp::FreeZero => "QubitRegisterOp::FreeZero",
        QubitRegisterOp::ExtractIndex => "QubitRegisterOp::ExtractIndex",
        QubitRegisterOp::InsertIndex => "QubitRegisterOp::InsertIndex",
        QubitRegisterOp::ExtractSlice => "QubitRegisterOp::ExtractSlice",
        QubitRegisterOp::InsertSlice => "QubitRegisterOp::InsertSlice",
        QubitRegisterOp::Length => "QubitRegisterOp::Length",
        QubitRegisterOp::Split => "QubitRegisterOp::Split",
        QubitRegisterOp::Join => "QubitRegisterOp::Join",
        QubitRegisterOp::Create => "QubitRegisterOp::Create",
        _ => "QubitRegisterOp::Unknown",
    }
}

fn check_qureg_op(
    func_name: &str,
    op_idx: usize,
    qreg_op: &QubitRegisterOp,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let op_tag = qureg_op_name(qreg_op);
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    match qreg_op {
        QubitRegisterOp::Alloc => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
        }
        QubitRegisterOp::Free | QubitRegisterOp::FreeZero => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 0, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
        }
        QubitRegisterOp::Length => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(32),
                errors,
            );
        }
        QubitRegisterOp::Split => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 2, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                1,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                1,
                &Type::QubitRegister { length: None },
                errors,
            );
        }
        QubitRegisterOp::Join => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                1,
                &Type::QubitRegister { length: None },
                errors,
            );
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
        }
        QubitRegisterOp::Create => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::QubitRegister { length: None },
                errors,
            );
        }
        _ => {}
    }
}

fn int_op_name(int_op: &IntOp) -> &'static str {
    match int_op {
        IntOp::Const1(_) => "IntOp::Const1",
        IntOp::Const8(_) => "IntOp::Const8",
        IntOp::Const16(_) => "IntOp::Const16",
        IntOp::Const32(_) => "IntOp::Const32",
        IntOp::Const64(_) => "IntOp::Const64",
        IntOp::Add => "IntOp::Add",
        IntOp::Sub => "IntOp::Sub",
        IntOp::Mul => "IntOp::Mul",
        IntOp::DivS => "IntOp::DivS",
        IntOp::DivU => "IntOp::DivU",
        IntOp::Pow => "IntOp::Pow",
        IntOp::And => "IntOp::And",
        IntOp::Or => "IntOp::Or",
        IntOp::Xor => "IntOp::Xor",
        IntOp::Not => "IntOp::Not",
        IntOp::MinS => "IntOp::MinS",
        IntOp::MinU => "IntOp::MinU",
        IntOp::MaxS => "IntOp::MaxS",
        IntOp::MaxU => "IntOp::MaxU",
        IntOp::Eq => "IntOp::Eq",
        IntOp::LtS => "IntOp::LtS",
        IntOp::LteS => "IntOp::LteS",
        IntOp::LtU => "IntOp::LtU",
        IntOp::LteU => "IntOp::LteU",
        IntOp::Abs => "IntOp::Abs",
        IntOp::RemS => "IntOp::RemS",
        IntOp::RemU => "IntOp::RemU",
        IntOp::Shl => "IntOp::Shl",
        IntOp::Shr => "IntOp::Shr",
        _ => "IntOp::Unknown",
    }
}

fn check_int_op(
    func_name: &str,
    op_idx: usize,
    int_op: &IntOp,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    let op_tag = int_op_name(int_op);
    match int_op {
        IntOp::Const1(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(1),
                errors,
            );
        }
        IntOp::Const8(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(8),
                errors,
            );
        }
        IntOp::Const16(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(16),
                errors,
            );
        }
        IntOp::Const32(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(32),
                errors,
            );
        }
        IntOp::Const64(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(64),
                errors,
            );
        }
        IntOp::Not | IntOp::Abs => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_same_int_bitwidth(func_name, op_idx, op_tag, &inputs, &outputs, errors);
        }
        IntOp::Eq | IntOp::LtS | IntOp::LteS | IntOp::LtU | IntOp::LteU => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_same_int_bitwidth_binary(func_name, op_idx, op_tag, &inputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(1),
                errors,
            );
        }
        IntOp::Shl | IntOp::Shr => {
            if inputs.is_empty() {
                errors.push(CheckError {
                    check_name: "types",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}]: {op_tag} expects at least 1 input, got {}",
                        inputs.len()
                    ),
                });
            }
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
        }
        _ => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_same_int_bitwidth_binary(func_name, op_idx, op_tag, &inputs, errors);
        }
    }
}

fn int_array_op_name(int_arr_op: &IntArrayOp<'_>) -> &'static str {
    match int_arr_op {
        IntArrayOp::ConstArray1(_) => "IntArrayOp::ConstArray1",
        IntArrayOp::ConstArray8(_) => "IntArrayOp::ConstArray8",
        IntArrayOp::ConstArray16(_) => "IntArrayOp::ConstArray16",
        IntArrayOp::ConstArray32(_) => "IntArrayOp::ConstArray32",
        IntArrayOp::ConstArray64(_) => "IntArrayOp::ConstArray64",
        IntArrayOp::Zero { .. } => "IntArrayOp::Zero",
        IntArrayOp::GetIndex => "IntArrayOp::GetIndex",
        IntArrayOp::SetIndex => "IntArrayOp::SetIndex",
        IntArrayOp::Length => "IntArrayOp::Length",
        IntArrayOp::Create => "IntArrayOp::Create",
        _ => "IntArrayOp::Unknown",
    }
}

fn check_int_array_op(
    func_name: &str,
    op_idx: usize,
    int_arr_op: &IntArrayOp<'_>,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    let op_tag = int_array_op_name(int_arr_op);
    match int_arr_op {
        IntArrayOp::ConstArray1(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_type_match(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::IntArray {
                    bits: 1,
                    length: None,
                },
                errors,
            );
        }
        IntArrayOp::ConstArray8(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_type_match(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::IntArray {
                    bits: 8,
                    length: None,
                },
                errors,
            );
        }
        IntArrayOp::Zero { bits } => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_type_match(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::IntArray {
                    bits: *bits,
                    length: None,
                },
                errors,
            );
        }
        IntArrayOp::GetIndex => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_type_match(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::IntArray {
                    bits: 0,
                    length: None,
                },
                errors,
            );
            check_type_match(func_name, op_idx, op_tag, &inputs, 1, &Type::int(0), errors);
        }
        IntArrayOp::Length => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_type_match(
                func_name,
                op_idx,
                op_tag,
                &inputs,
                0,
                &Type::IntArray {
                    bits: 0,
                    length: None,
                },
                errors,
            );
        }
        _ => {}
    }
}

fn float_op_name(float_op: &FloatOp) -> &'static str {
    match float_op {
        FloatOp::Const32(_) => "FloatOp::Const32",
        FloatOp::Const64(_) => "FloatOp::Const64",
        FloatOp::Add => "FloatOp::Add",
        FloatOp::Sub => "FloatOp::Sub",
        FloatOp::Mul => "FloatOp::Mul",
        FloatOp::Pow => "FloatOp::Pow",
        FloatOp::Eq => "FloatOp::Eq",
        FloatOp::Lt => "FloatOp::Lt",
        FloatOp::Lte => "FloatOp::Lte",
        FloatOp::Sqrt => "FloatOp::Sqrt",
        FloatOp::Abs => "FloatOp::Abs",
        FloatOp::Ceil => "FloatOp::Ceil",
        FloatOp::Floor => "FloatOp::Floor",
        FloatOp::IsNan => "FloatOp::IsNan",
        FloatOp::IsInf => "FloatOp::IsInf",
        FloatOp::Exp => "FloatOp::Exp",
        FloatOp::Log => "FloatOp::Log",
        FloatOp::Sin => "FloatOp::Sin",
        FloatOp::Cos => "FloatOp::Cos",
        FloatOp::Tan => "FloatOp::Tan",
        FloatOp::Asin => "FloatOp::Asin",
        FloatOp::Acos => "FloatOp::Acos",
        FloatOp::Atan => "FloatOp::Atan",
        FloatOp::Atan2 => "FloatOp::Atan2",
        FloatOp::Sinh => "FloatOp::Sinh",
        FloatOp::Cosh => "FloatOp::Cosh",
        FloatOp::Tanh => "FloatOp::Tanh",
        FloatOp::Asinh => "FloatOp::Asinh",
        FloatOp::Acosh => "FloatOp::Acosh",
        FloatOp::Atanh => "FloatOp::Atanh",
        FloatOp::Max => "FloatOp::Max",
        FloatOp::Min => "FloatOp::Min",
        _ => "FloatOp::Unknown",
    }
}

fn check_float_op(
    func_name: &str,
    op_idx: usize,
    float_op: &FloatOp,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    let op_tag = float_op_name(float_op);
    match float_op {
        FloatOp::Const32(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::Float {
                    precision: FloatPrecision::Float32,
                },
                errors,
            );
        }
        FloatOp::Const64(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::Float {
                    precision: FloatPrecision::Float64,
                },
                errors,
            );
        }
        FloatOp::Eq | FloatOp::Lt | FloatOp::Lte => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_same_float_precision_binary(func_name, op_idx, op_tag, &inputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(1),
                errors,
            );
        }
        FloatOp::IsNan | FloatOp::IsInf => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::int(1),
                errors,
            );
        }
        FloatOp::Add
        | FloatOp::Sub
        | FloatOp::Mul
        | FloatOp::Atan2
        | FloatOp::Pow
        | FloatOp::Max
        | FloatOp::Min => {
            expect_count(func_name, op_idx, op_tag, 2, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            check_same_float_precision_binary(func_name, op_idx, op_tag, &inputs, errors);
        }
        _ => {
            expect_count(func_name, op_idx, op_tag, 1, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            for i in 0..inputs.len() {
                expect_type(
                    func_name,
                    op_idx,
                    op_tag,
                    &inputs,
                    i,
                    &Type::Float {
                        precision: FloatPrecision::Float64,
                    },
                    errors,
                );
            }
            for i in 0..outputs.len() {
                expect_type(
                    func_name,
                    op_idx,
                    op_tag,
                    &outputs,
                    i,
                    &Type::Float {
                        precision: FloatPrecision::Float64,
                    },
                    errors,
                );
            }
        }
    }
}

fn check_float_array_op(
    func_name: &str,
    op_idx: usize,
    float_arr_op: &jeff::reader::optype::FloatArrayOp<'_>,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let outputs = collect_types(op, jeff::Direction::Outgoing);
    let op_tag = "FloatArrayOp";
    match float_arr_op {
        jeff::reader::optype::FloatArrayOp::Const32(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::float_array(FloatPrecision::Float32, None),
                errors,
            );
        }
        jeff::reader::optype::FloatArrayOp::Const64(_) => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::float_array(FloatPrecision::Float64, None),
                errors,
            );
        }
        jeff::reader::optype::FloatArrayOp::Zero { precision } => {
            expect_count(func_name, op_idx, op_tag, 0, &inputs, errors);
            expect_count(func_name, op_idx, op_tag, 1, &outputs, errors);
            expect_type(
                func_name,
                op_idx,
                op_tag,
                &outputs,
                0,
                &Type::FloatArray {
                    precision: *precision,
                    length: None,
                },
                errors,
            );
        }
        _ => {}
    }
}

fn check_control_flow_op(
    func_name: &str,
    op_idx: usize,
    cf_op: &ControlFlowOp<'_>,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let inputs = collect_types(op, jeff::Direction::Incoming);
    let _ = cf_op;
    let op_tag = "ControlFlowOp";
    if !inputs.is_empty() {
        expect_type(func_name, op_idx, op_tag, &inputs, 0, &Type::int(0), errors);
    }
}

fn check_func_op(
    func_name: &str,
    op_idx: usize,
    func_op: &FuncOp,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let _ = (func_name, op_idx, func_op, op, errors);
}

fn expect_count(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    expected: usize,
    actual: &[(usize, u32, Type)],
    errors: &mut Vec<CheckError>,
) {
    if actual.len() != expected {
        errors.push(CheckError {
            check_name: "types",
            message: format!(
                "Function '{func_name}', op[{op_idx}]: {op_tag} expects {expected} values, got {}",
                actual.len()
            ),
        });
    }
}

fn check_type_match(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    values: &[(usize, u32, Type)],
    idx: usize,
    expected: &Type,
    errors: &mut Vec<CheckError>,
) {
    if idx >= values.len() {
        return;
    }
    let actual = &values[idx].2;
    let ok = match (expected, actual) {
        (
            Type::IntArray {
                bits: eb,
                length: _,
            },
            Type::IntArray { bits: _, length: _ },
        ) if *eb == 0 => true,
        (
            Type::IntArray {
                bits: eb,
                length: _,
            },
            Type::IntArray {
                bits: ab,
                length: _,
            },
        ) => eb == ab,
        (
            Type::FloatArray {
                precision: ep,
                length: _,
            },
            Type::FloatArray {
                precision: ap,
                length: _,
            },
        ) => ep == ap,
        (Type::QubitRegister { length: _ }, Type::QubitRegister { length: _ }) => true,
        (Type::Int { bits: eb }, Type::Int { bits: _ }) if *eb == 0 => true,
        _ => actual == expected,
    };
    if !ok {
        errors.push(CheckError {
            check_name: "types",
            message: format!(
                "Function '{func_name}', op[{op_idx}]: {op_tag} value[{idx}] expected {expected}, got {actual}"
            ),
        });
    }
}

fn expect_type(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    values: &[(usize, u32, Type)],
    idx: usize,
    expected: &Type,
    errors: &mut Vec<CheckError>,
) {
    if idx >= values.len() {
        return;
    }
    let ty = &values[idx].2;
    if ty != expected {
        errors.push(CheckError {
            check_name: "types",
            message: format!(
                "Function '{func_name}', op[{op_idx}]: {op_tag} value[{idx}] expected {expected}, got {ty}"
            ),
        });
    }
}

fn check_same_int_bitwidth(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    inputs: &[(usize, u32, Type)],
    outputs: &[(usize, u32, Type)],
    errors: &mut Vec<CheckError>,
) {
    if inputs.is_empty() || outputs.is_empty() {
        return;
    }
    let first_input_bits = match &inputs[0].2 {
        Type::Int { bits } => *bits,
        _ => return,
    };
    for (i, input) in inputs.iter().enumerate() {
        match &input.2 {
            Type::Int { bits } if *bits == first_input_bits => {}
            Type::Int { bits } => {
                errors.push(CheckError {
                    check_name: "types",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}]: {op_tag} input[{i}] has bitwidth {bits}, expected {first_input_bits}"
                    ),
                });
            }
            _ => {
                errors.push(CheckError {
                    check_name: "types",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}]: {op_tag} input[{i}] expected Int type"
                    ),
                });
            }
        }
    }
}

fn check_same_int_bitwidth_binary(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    inputs: &[(usize, u32, Type)],
    errors: &mut Vec<CheckError>,
) {
    if inputs.len() < 2 {
        return;
    }
    let (ty0, ty1) = (&inputs[0].2, &inputs[1].2);
    match (ty0, ty1) {
        (Type::Int { bits: b0 }, Type::Int { bits: b1 }) => {
            if b0 != b1 {
                errors.push(CheckError {
                    check_name: "types",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}]: {op_tag} inputs have mismatched bitwidths: {ty0} vs {ty1}"
                    ),
                });
            }
        }
        _ => {
            errors.push(CheckError {
                check_name: "types",
                message: format!(
                    "Function '{func_name}', op[{op_idx}]: {op_tag} expected Int inputs, got {ty0} and {ty1}"
                ),
            });
        }
    }
}

fn check_same_float_precision_binary(
    func_name: &str,
    op_idx: usize,
    op_tag: &str,
    inputs: &[(usize, u32, Type)],
    errors: &mut Vec<CheckError>,
) {
    if inputs.len() < 2 {
        return;
    }
    let (ty0, ty1) = (&inputs[0].2, &inputs[1].2);
    match (ty0, ty1) {
        (Type::Float { precision: p0 }, Type::Float { precision: p1 }) => {
            if p0 != p1 {
                errors.push(CheckError {
                    check_name: "types",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}]: {op_tag} inputs have mismatched precision: {ty0} vs {ty1}"
                    ),
                });
            }
        }
        _ => {
            errors.push(CheckError {
                check_name: "types",
                message: format!(
                    "Function '{func_name}', op[{op_idx}]: {op_tag} expected Float inputs, got {ty0} and {ty1}"
                ),
            });
        }
    }
}
