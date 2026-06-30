//! Checks for value ordering, bounds, and linearity constraints.

use std::collections::HashSet;

use jeff::reader::optype::{ControlFlowOp, OpType};
use jeff::reader::{FunctionDefinition, ReadError, Region, ValueId};
use jeff::types::Type;

use crate::analysis::build_value_stats;
use crate::VerificationError;

/// Check value ordering, out-of-bounds references, and linearity for a function definition.
pub fn verify_value_checks(def: FunctionDefinition<'_>, errors: &mut Vec<VerificationError>) {
    let values = def.values();
    let num_values = values.len();

    check_region_ordering(def.body(), &HashSet::new(), errors);

    match build_value_stats(def.body(), num_values) {
        Ok(stats) => {
            for (id, value) in values.iter() {
                let stat = &stats[id as usize];
                if stat.producers > 1 {
                    errors.push(VerificationError::ValueProducedMultipleTimes {
                        value_id: id,
                        producers: stat.producers,
                    });
                }
                if is_linear(value.ty()) {
                    if stat.consumers > 1 {
                        errors.push(VerificationError::LinearValueConsumedMultipleTimes {
                            value_id: id,
                            consumers: stat.consumers,
                        });
                    }
                    if stat.consumers == 0 && stat.producers > 0 {
                        errors.push(VerificationError::LinearValueNeverConsumed { value_id: id });
                    }
                }
            }
        }
        Err(e) => push_oob(e, errors),
    }
}

fn is_linear(ty: Type) -> bool {
    matches!(ty, Type::Qubit | Type::QubitRegister { .. })
}

fn push_oob(e: ReadError, errors: &mut Vec<VerificationError>) {
    if let ReadError::ValueOutOfBounds { idx, count } = e {
        errors.push(VerificationError::ValueOutOfBounds {
            value_id: idx,
            value_count: count,
        });
    }
}

fn check_region_ordering(
    region: Region<'_>,
    outer_defined: &HashSet<ValueId>,
    errors: &mut Vec<VerificationError>,
) {
    let mut defined: HashSet<ValueId> = outer_defined.clone();

    for result in region.sources() {
        match result {
            Ok(v) => {
                defined.insert(v.id());
            }
            Err(e) => push_oob(e, errors),
        }
    }

    for op in region.operations() {
        for result in op.inputs() {
            match result {
                Ok(v) if !defined.contains(&v.id()) => {
                    errors.push(VerificationError::UsedBeforeDefined { value_id: v.id() });
                }
                Ok(_) => {}
                Err(e) => push_oob(e, errors),
            }
        }

        for result in op.outputs() {
            match result {
                Ok(v) => {
                    defined.insert(v.id());
                }
                Err(e) => push_oob(e, errors),
            }
        }

        if let OpType::ControlFlowOp(cf_op) = op.op_type() {
            check_cf_ordering(cf_op.as_ref(), &defined, errors);
        }
    }

    for result in region.targets() {
        match result {
            Ok(v) if !defined.contains(&v.id()) => {
                errors.push(VerificationError::UsedBeforeDefined { value_id: v.id() });
            }
            Ok(_) => {}
            Err(e) => push_oob(e, errors),
        }
    }
}

fn check_cf_ordering(
    cf_op: &ControlFlowOp<'_>,
    outer_defined: &HashSet<ValueId>,
    errors: &mut Vec<VerificationError>,
) {
    match cf_op {
        ControlFlowOp::For { region } => check_region_ordering(*region, outer_defined, errors),
        ControlFlowOp::While { before, after } => {
            check_region_ordering(*before, outer_defined, errors);
            check_region_ordering(*after, outer_defined, errors);
        }
        ControlFlowOp::Switch(switch_op) => {
            for branch in switch_op.branches() {
                check_region_ordering(branch, outer_defined, errors);
            }
            if let Some(default) = switch_op.default_branch() {
                check_region_ordering(default, outer_defined, errors);
            }
        }
    }
}
