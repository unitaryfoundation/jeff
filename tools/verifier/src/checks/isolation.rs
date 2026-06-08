use std::collections::HashSet;

use jeff::reader::optype::{ControlFlowOp, OpType};
use jeff::reader::Module;

use super::{Check, CheckError};

pub struct IsolationCheck;

impl Check for IsolationCheck {
    fn name(&self) -> &'static str {
        "isolation"
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
            check_region_isolation(&func_name, body, &mut errors);
        }

        errors
    }
}

fn check_region_isolation(
    func_name: &str,
    region: jeff::reader::Region<'_>,
    errors: &mut Vec<CheckError>,
) {
    for (op_idx, op) in region.operations().enumerate() {
        check_op_isolation(func_name, op_idx, op, errors);
    }
}

fn check_op_isolation(
    func_name: &str,
    op_idx: usize,
    op: jeff::reader::Operation<'_>,
    errors: &mut Vec<CheckError>,
) {
    let op_type = op.op_type();
    if let OpType::ControlFlowOp(cf_op) = op_type {
        let cf_op = cf_op.as_ref();
        match cf_op {
            ControlFlowOp::For { ref region } => {
                check_nested_region(func_name, op_idx, "for-body", *region, errors);
            }
            ControlFlowOp::While {
                ref condition,
                ref body,
            } => {
                check_nested_region(func_name, op_idx, "while-condition", *condition, errors);
                check_nested_region(func_name, op_idx, "while-body", *body, errors);
            }
            ControlFlowOp::DoWhile {
                ref body,
                ref condition,
            } => {
                check_nested_region(func_name, op_idx, "dowhile-body", *body, errors);
                check_nested_region(func_name, op_idx, "dowhile-condition", *condition, errors);
            }
            ControlFlowOp::Switch(switch) => {
                for (i, branch) in switch.branches().enumerate() {
                    check_nested_region(
                        func_name,
                        op_idx,
                        &format!("switch-branch[{i}]"),
                        branch,
                        errors,
                    );
                }
                if let Some(default) = switch.default_branch() {
                    check_nested_region(func_name, op_idx, "switch-default", default, errors);
                }
            }
        }
    }
}

fn check_nested_region(
    func_name: &str,
    op_idx: usize,
    label: &str,
    region: jeff::reader::Region<'_>,
    errors: &mut Vec<CheckError>,
) {
    let sources: HashSet<u32> = region
        .sources()
        .filter_map(|r| r.ok())
        .map(|v| v.id())
        .collect();

    let defined_inside: HashSet<u32> = region
        .operations()
        .flat_map(|op| op.outputs().filter_map(|r| r.ok()).map(|v| v.id()))
        .collect();

    let mut allowed = sources;
    allowed.extend(&defined_inside);

    for inner_op in region.operations() {
        for result in inner_op.inputs() {
            let Ok(v) = result else { continue };
            if !allowed.contains(&v.id()) {
                errors.push(CheckError {
                    check_name: "isolation",
                    message: format!(
                        "Function '{func_name}', op[{op_idx}] ({label}): value {} used inside region but is not a region source or defined within the region",
                        v.id()
                    ),
                });
            }
        }
    }
}
