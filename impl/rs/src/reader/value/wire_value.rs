//! Wire values representing typed hyperedges in dataflow regions.

use super::ValueId;
use crate::capnp::jeff_capnp;
use crate::reader::metadata::sealed::HasMetadataSealed;
use crate::reader::string_table::StringTable;

use crate::types::Type;

/// Wire type and associated metadata.
///
/// Ports in the dataflow graph reference these values by their index in the
/// function's value array.
///
/// This corresponds to a jeff format `WireValue`, with a defined ID identifying
/// it in a [`ValueTable`][super::ValueTable].
#[derive(Clone, Copy, Debug)]
pub struct WireValue<'a> {
    /// The ID of this value in the function's [`ValueTable`][super::ValueTable].
    id: ValueId,
    /// Type of the hyperedge.
    pub(super) value_type: Type,
    /// Metadata associated with the value.
    pub(super) metadata: capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned>,
    /// Module-level register of reused strings.
    pub(super) strings: StringTable<'a>,
}

impl<'a> WireValue<'a> {
    /// Create a new function view from a capnp reader.
    pub(crate) fn read_capnp(
        id: super::ValueId,
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

    /// Returns the ID of this value in the containing function's [`ValueTable`][super::ValueTable].
    pub fn id(&self) -> ValueId {
        self.id
    }

    /// Returns the type of this value.
    pub fn ty(&self) -> Type {
        self.value_type
    }
}

impl<'a> HasMetadataSealed for WireValue<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.metadata
    }
}
