//! "Values" represent wire types in the jeff language with associated metadata.
//!
//! There are two types of values:
//!
//! - [`WireValue`]s that correspond to typed hyperedges in dataflow regions.
//! - [`FunctionIOValue`]s, describing the inputs and outputs of a function.
//!
//! All regions inside a function share a single [`ValueTable`] listing all the
//! hyperedges in the function. These are indexed by their [`ValueId`]s.

mod function_io;
mod wire_value;

pub use function_io::FunctionIOValue;
pub use wire_value::WireValue;

use crate::capnp::jeff_capnp;

use super::string_table::StringTable;
use super::ReadError;

/// The ID of a value hyperedge in the function's value table.
pub type ValueId = u32;

/// Table of values / typed hyperedges contained in a function.
#[derive(Clone, Copy, Debug)]
pub struct ValueTable<'a> {
    /// Internal capnproto value table.
    values: capnp::struct_list::Reader<'a, jeff_capnp::value::Owned>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
}

impl<'a> ValueTable<'a> {
    /// Create a new value table view from a capnp reader.
    pub(crate) fn read_capnp(
        values: capnp::struct_list::Reader<'a, jeff_capnp::value::Owned>,
        strings: StringTable<'a>,
    ) -> Self {
        Self { values, strings }
    }

    /// Returns the wire value at the given index.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the index is out of bounds.
    pub fn get(&self, idx: ValueId) -> Result<WireValue<'a>, ReadError> {
        let value = self
            .values
            .try_get(idx)
            .ok_or_else(|| ReadError::ValueOutOfBounds {
                idx,
                count: self.len(),
            })?;

        Ok(WireValue::read_capnp(idx, value, self.strings))
    }

    /// Returns an iterator over the wire values in this table.
    pub fn iter(&self) -> impl Iterator<Item = (ValueId, WireValue<'a>)> + '_ {
        self.values.iter().enumerate().map(move |(idx, value)| {
            (
                idx as ValueId,
                WireValue::read_capnp(idx as ValueId, value, self.strings),
            )
        })
    }

    /// Returns the number of strings in this table.
    pub fn len(&self) -> usize {
        self.values.len() as usize
    }

    /// Returns `true` if the table is empty.
    pub fn is_empty(&self) -> bool {
        self.values.len() == 0
    }
}
