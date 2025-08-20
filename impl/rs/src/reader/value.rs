//! "Values" represent typed hyperedges in the jeff language.

use crate::capnp::jeff_capnp;

use super::metadata::sealed::HasMetadataSealed;
use super::string_table::StringTable;
use super::ReadError;
use crate::types::Type;

/// The ID of a value hyperedge in the function's value table.
pub type ValueId = u32;

/// Hyperedge type and associated metadata.
///
/// Ports in the dataflow graph reference these values by their index in the
/// function's value array.
#[derive(Clone, Copy, Debug)]
pub struct Value<'a> {
    /// The ID of this value in the function's value table.
    ///
    /// If the value is the input/output of a function declaration, this will be
    /// `None`.
    id: Option<ValueId>,
    /// Type of the hyperedge.
    value_type: Type,
    /// Metadata associated with the value.
    metadata: capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
}

impl<'a> Value<'a> {
    /// Create a new function view from a capnp reader.
    pub(crate) fn read_capnp(
        id: Option<ValueId>,
        value: jeff_capnp::value::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Self {
        let value_type = value
            .get_type()
            .map(Type::read_capnp)
            .expect("Type should be present");
        let metadata = value.get_metadata().expect("Metadata should be present");
        Self {
            id,
            value_type,
            metadata,
            strings,
        }
    }

    /// Returns the ID of this value in the function's value table.
    ///
    /// If the value is the input/output of a function declaration, this will be
    /// `None`.
    pub fn id(&self) -> Option<ValueId> {
        self.id
    }

    /// Returns the type of this value.
    pub fn ty(&self) -> Type {
        self.value_type
    }
}

impl<'a> HasMetadataSealed for Value<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.metadata
    }
}

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

    /// Returns the string at the given index.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the index is out of bounds.
    pub fn get(&self, idx: ValueId) -> Result<Value<'a>, ReadError> {
        let value = self
            .values
            .try_get(idx)
            .ok_or_else(|| ReadError::ValueOutOfBounds {
                idx,
                count: self.len(),
            })?;

        Ok(Value::read_capnp(Some(idx), value, self.strings))
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
