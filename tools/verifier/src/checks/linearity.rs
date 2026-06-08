use std::collections::HashSet;

use jeff::reader::optype::{ControlFlowOp, OpType};
use jeff::reader::Module;
use jeff::types::Type;

use super::{Check, CheckError};

pub struct LinearityCheck;

impl Check for LinearityCheck {
    fn name(&self) -> &'static str {
        "linearity"
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
            check_region_linearity(&func_name, body, &mut errors);
        }

        errors
    }
}

fn is_linear_type(ty: &Type) -> bool {
    matches!(ty, Type::Qubit | Type::QubitRegister { .. })
}

fn check_region_linearity(
    func_name: &str,
    region: jeff::reader::Region<'_>,
    errors: &mut Vec<CheckError>,
) {
    let mut qubit_inputs: HashSet<u32> = HashSet::new();
    let mut qubit_outputs: HashSet<u32> = HashSet::new();

    for source in region.sources() {
        let Ok(v) = source else { continue };
        if is_linear_type(&v.ty()) {
            qubit_outputs.insert(v.id());
        }
    }

    for (op_idx, op) in region.operations().enumerate() {
        for result in op.inputs() {
            let Ok(v) = result else { continue };
            if is_linear_type(&v.ty()) {
                if !qubit_inputs.insert(v.id()) {
                    errors.push(CheckError {
                        check_name: "linearity",
                        message: format!(
                            "Function '{func_name}', op[{op_idx}]: qubit/qureg value {} consumed more than once",
                            v.id()
                        ),
                    });
                }
            }
        }

        for result in op.outputs() {
            let Ok(v) = result else { continue };
            if is_linear_type(&v.ty()) {
                qubit_outputs.insert(v.id());
            }
        }

        check_nested_regions(func_name, op_idx, &op, errors);
    }

    for target in region.targets() {
        let Ok(v) = target else { continue };
        if is_linear_type(&v.ty()) {
            qubit_inputs.insert(v.id());
        }
    }

    for q in &qubit_outputs {
        if !qubit_inputs.contains(q) {
            errors.push(CheckError {
                check_name: "linearity",
                message: format!(
                    "Function '{}': qubit/qureg value {} is defined but never consumed (must be destructively measured or freed)",
                    func_name, q
                ),
            });
        }
    }
}

fn check_nested_regions(
    func_name: &str,
    _op_idx: usize,
    op: &jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let op_type = op.op_type();
    if let OpType::ControlFlowOp(cf_op) = op_type {
        let cf_op = cf_op.as_ref();
        match cf_op {
            ControlFlowOp::For { ref region } => {
                check_region_linearity(func_name, *region, errors);
            }
            ControlFlowOp::While {
                ref condition,
                ref body,
            } => {
                check_region_linearity(func_name, *condition, errors);
                check_region_linearity(func_name, *body, errors);
            }
            ControlFlowOp::DoWhile {
                ref body,
                ref condition,
            } => {
                check_region_linearity(func_name, *body, errors);
                check_region_linearity(func_name, *condition, errors);
            }
            ControlFlowOp::Switch(switch) => {
                for branch in switch.branches() {
                    check_region_linearity(func_name, branch, errors);
                }
                if let Some(default) = switch.default_branch() {
                    check_region_linearity(func_name, default, errors);
                }
            }
        }
    }
}
