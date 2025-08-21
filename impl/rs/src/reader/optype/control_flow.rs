//! Control-flow operations.

use crate::reader::string_table::StringTable;
use crate::reader::value::ValueTable;
use crate::{jeff_capnp, reader};

/// A structured control-flow operation.
#[derive(Clone, Copy, Debug)]
#[allow(clippy::large_enum_variant)]
pub enum ControlFlowOp<'a> {
    /// Switch statement.
    ///
    /// The first input to the switch is an integer that selects the branch by
    /// index. The operation has a region for every branch, together with an
    /// optional default region. If there is no default region, it is an error
    /// if the index does not match any branch.
    Switch(SwitchOp<'a>),
    /// For loop.
    ///
    /// The loop iterates from start to stop (exclusive) by step.
    /// The region is the loop body that is executed once for each iteration.
    /// The loop maintains a state consisting of any number of values.
    /// Each iteration receives the state from the previous iteration,
    /// or the initial state for the first iteration.
    /// When the loop finishes, the final state is returned.
    /// Iterations also have access to the current iteration value.
    For {
        /// Internal DFG of the loop.
        region: reader::Region<'a>,
    },
    /// While loop.
    ///
    /// The condition is checked before each iteration.
    /// If the condition is true, the loop body is executed.
    /// The loop maintains a state consisting of any number of values.
    /// Each iteration receives the state from the previous iteration,
    /// or the initial state for the first iteration.
    /// When the loop finishes, the final state is returned.
    While {
        /// The condition that determines whether to continue looping.
        condition: reader::Region<'a>,
        /// The body that is executed on each iteration.
        body: reader::Region<'a>,
    },
    /// Do-while loop.
    ///
    /// The loop body is executed once, then the condition is checked.
    /// If the condition is true, the loop body is executed again.
    /// The loop maintains a state consisting of any number of values.
    /// Each iteration receives the state from the previous iteration,
    /// or the initial state for the first iteration.
    /// When the loop finishes, the final state is returned.
    DoWhile {
        /// The body that is executed on each iteration.
        body: reader::Region<'a>,
        /// The condition that determines whether to continue looping.
        condition: reader::Region<'a>,
    },
}

/// A function call operation.
#[derive(Clone, Copy, Debug)]
pub struct FuncOp {
    /// The function index to call in the module.
    pub func_idx: u16,
}

/// A switch statement.
#[derive(Clone, Copy, Debug)]
pub struct SwitchOp<'a> {
    /// The branches of the switch statement.
    branches: capnp::struct_list::Reader<'a, jeff_capnp::region::Owned>,
    /// An optional default branch to take if the index is out of bounds.
    default: Option<reader::Region<'a>>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
    /// Function-level register of typed hyperedges.
    values: ValueTable<'a>,
}

impl<'a> ControlFlowOp<'a> {
    /// Create a new control-flow operation from a capnp reader.
    pub(crate) fn read_capnp(
        control_flow: jeff_capnp::scf_op::Reader<'a>,
        strings: StringTable<'a>,
        values: ValueTable<'a>,
    ) -> Self {
        match control_flow
            .which()
            .expect("Control flow should be present")
        {
            jeff_capnp::scf_op::Switch(switch) => {
                ControlFlowOp::Switch(SwitchOp::read_capnp(switch, strings, values))
            }
            jeff_capnp::scf_op::For(for_loop) => ControlFlowOp::For {
                region: reader::Region::read_capnp(
                    for_loop.expect("For loop should be present"),
                    strings,
                    values,
                ),
            },
            jeff_capnp::scf_op::While(while_loop) => ControlFlowOp::While {
                condition: reader::Region::read_capnp(
                    while_loop
                        .get_condition()
                        .expect("Condition should be present"),
                    strings,
                    values,
                ),
                body: reader::Region::read_capnp(
                    while_loop.get_body().expect("Body should be present"),
                    strings,
                    values,
                ),
            },
            jeff_capnp::scf_op::DoWhile(dowhile_loop) => ControlFlowOp::DoWhile {
                body: reader::Region::read_capnp(
                    dowhile_loop.get_body().expect("Body should be present"),
                    strings,
                    values,
                ),
                condition: reader::Region::read_capnp(
                    dowhile_loop
                        .get_condition()
                        .expect("Condition should be present"),
                    strings,
                    values,
                ),
            },
        }
    }
}

impl<'a> SwitchOp<'a> {
    /// Create a new switch operation from a capnp reader.
    pub(crate) fn read_capnp(
        switch: jeff_capnp::scf_op::switch::Reader<'a>,
        strings: StringTable<'a>,
        values: ValueTable<'a>,
    ) -> Self {
        let branches = switch.get_branches().expect("Branches should be present");

        let default = switch
            .get_default()
            .ok()
            .map(|r| reader::Region::read_capnp(r, strings, values));

        Self {
            branches,
            default,
            strings,
            values,
        }
    }

    /// Returns an iterator over the branches of this switch statement.
    pub fn branches(&self) -> impl Iterator<Item = reader::Region<'a>> {
        let string_table = self.strings;
        let value_table = self.values;
        self.branches
            .iter()
            .map(move |r| reader::Region::read_capnp(r, string_table, value_table))
    }

    /// Returns the number of branches in this switch statement.
    pub fn branch_count(&self) -> usize {
        self.branches.len() as usize
    }

    /// Returns the `n`-th branch of this switch statement.
    ///
    /// # Panics
    /// Panics if `n` is equal or greater than [`SwitchOp::branch_count`].
    pub fn branch(&self, n: usize) -> reader::Region<'a> {
        reader::Region::read_capnp(self.branches.get(n as u32), self.strings, self.values)
    }

    /// Returns the `n`-th branch of this switch statement.
    ///
    /// Returns `None` if `n` is equal or greater than [`SwitchOp::branch_count`].
    pub fn try_branch(&self, n: usize) -> Option<reader::Region<'a>> {
        let r = self.branches.try_get(n as u32)?;
        Some(reader::Region::read_capnp(r, self.strings, self.values))
    }

    /// Returns the default branch of this switch statement.
    ///
    /// Returns `None` if there is no default branch.
    pub fn default_branch(&self) -> Option<reader::Region<'_>> {
        self.default
    }
}
