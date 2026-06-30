//! Information collection over jeff regions.
//!
//! This module traverses a function's dataflow graph to gather statistics
//! used by the verification passes.

use jeff::reader::optype::{ControlFlowOp, OpType};
use jeff::reader::{ReadError, Region};

/// Producer and consumer counts for a single value.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct ValueStats {
    /// Number of operations that produce this value.
    pub producers: u32,
    /// Number of operations that consume this value.
    pub consumers: u32,
}

/// Walk `region` recursively and accumulate producer/consumer counts into `stats`.
///
/// The slice must be pre-allocated with one entry per value in the function's value table.
pub fn collect_value_stats(region: Region<'_>, stats: &mut [ValueStats]) -> Result<(), ReadError> {
    for value in region.sources() {
        stats[value?.id() as usize].producers += 1;
    }

    for value in region.targets() {
        stats[value?.id() as usize].consumers += 1;
    }

    for op in region.operations() {
        for value in op.inputs() {
            stats[value?.id() as usize].consumers += 1;
        }

        for value in op.outputs() {
            stats[value?.id() as usize].producers += 1;
        }

        if let OpType::ControlFlowOp(cf_op) = op.op_type() {
            collect_cf_value_stats(cf_op.as_ref(), stats)?;
        }
    }

    Ok(())
}

fn collect_cf_value_stats(
    cf_op: &ControlFlowOp<'_>,
    stats: &mut [ValueStats],
) -> Result<(), ReadError> {
    match cf_op {
        ControlFlowOp::For { region } => {
            collect_value_stats(*region, stats)?;
        }
        ControlFlowOp::While { before, after } => {
            collect_value_stats(*before, stats)?;
            collect_value_stats(*after, stats)?;
        }
        ControlFlowOp::Switch(switch_op) => {
            for branch in switch_op.branches() {
                collect_value_stats(branch, stats)?;
            }
            if let Some(default) = switch_op.default_branch() {
                collect_value_stats(default, stats)?;
            }
        }
    }
    Ok(())
}

/// Build a [`Vec<ValueStats>`] with one entry per value in the function's value table.
pub fn build_value_stats(
    region: Region<'_>,
    num_values: usize,
) -> Result<Vec<ValueStats>, ReadError> {
    let mut stats = vec![ValueStats::default(); num_values];
    collect_value_stats(region, &mut stats)?;
    Ok(stats)
}
