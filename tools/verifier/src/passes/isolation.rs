//! Checks that nested regions are isolated from outer scopes (IsolatedFromAbove).

use std::collections::HashSet;

use jeff::reader::optype::{ControlFlowOp, OpType};
use jeff::reader::{FunctionDefinition, Region, ValueId};

use crate::VerificationError;

/// Check that no operation inside a nested region directly references a value from an outer scope.
pub fn verify_isolation(def: FunctionDefinition<'_>, errors: &mut Vec<VerificationError>) {
    check_region_isolation(def.body(), &HashSet::new(), errors);
}

fn check_region_isolation(
    region: Region<'_>,
    outer_values: &HashSet<ValueId>,
    errors: &mut Vec<VerificationError>,
) {
    let mut locally_defined: HashSet<ValueId> = region
        .sources()
        .filter_map(|r| r.ok())
        .map(|v| v.id())
        .collect();

    for op in region.operations() {
        for input in op.inputs().filter_map(|r| r.ok()) {
            if outer_values.contains(&input.id()) {
                errors.push(VerificationError::IsolationViolation {
                    value_id: input.id(),
                });
            }
        }

        for output in op.outputs().filter_map(|r| r.ok()) {
            locally_defined.insert(output.id());
        }

        if let OpType::ControlFlowOp(cf_op) = op.op_type() {
            let new_outer: HashSet<ValueId> = outer_values
                .iter()
                .chain(locally_defined.iter())
                .cloned()
                .collect();
            check_cf_isolation(cf_op.as_ref(), &new_outer, errors);
        }
    }

    for target in region.targets().filter_map(|r| r.ok()) {
        if outer_values.contains(&target.id()) {
            errors.push(VerificationError::IsolationViolation {
                value_id: target.id(),
            });
        }
    }
}

fn check_cf_isolation(
    cf_op: &ControlFlowOp<'_>,
    outer_values: &HashSet<ValueId>,
    errors: &mut Vec<VerificationError>,
) {
    match cf_op {
        ControlFlowOp::For { region } => {
            check_region_isolation(*region, outer_values, errors);
        }
        ControlFlowOp::While { condition, body } => {
            check_region_isolation(*condition, outer_values, errors);
            check_region_isolation(*body, outer_values, errors);
        }
        ControlFlowOp::DoWhile { body, condition } => {
            check_region_isolation(*body, outer_values, errors);
            check_region_isolation(*condition, outer_values, errors);
        }
        ControlFlowOp::Switch(switch_op) => {
            for branch in switch_op.branches() {
                check_region_isolation(branch, outer_values, errors);
            }
            if let Some(default) = switch_op.default_branch() {
                check_region_isolation(default, outer_values, errors);
            }
        }
    }
}
