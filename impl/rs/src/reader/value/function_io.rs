//! Input/output types and metadata for functions.

use crate::capnp::jeff_capnp;
use crate::reader::metadata::sealed::HasMetadataSealed;
use crate::reader::string_table::StringTable;

use crate::types::Type;

use super::WireValue;

/// Input/output type for a function, with associated metadata.
///
/// This corresponds to a jeff format `Value`.
#[derive(Clone, Copy, Debug)]
pub struct FunctionIOValue<'a> {
    /// Type of the hyperedge.
    value_type: Type,
    /// Metadata associated with the value.
    metadata: capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
}

impl<'a> FunctionIOValue<'a> {
    /// Create a new function view from a capnp reader.
    pub(crate) fn read_capnp(
        value: jeff_capnp::value::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Self {
        let value_type = value
            .get_type()
            .map(Type::read_capnp)
            .expect("Type should be present");
        let metadata = value.get_metadata().expect("Metadata should be present");
        Self {
            value_type,
            metadata,
            strings,
        }
    }

    /// Returns the type of this value.
    pub fn ty(&self) -> Type {
        self.value_type
    }
}

impl<'a> HasMetadataSealed for FunctionIOValue<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.metadata
    }
}

impl<'a> From<WireValue<'a>> for FunctionIOValue<'a> {
    fn from(wire_value: WireValue<'a>) -> Self {
        Self {
            value_type: wire_value.value_type,
            metadata: wire_value.metadata,
            strings: wire_value.strings,
        }
    }
}
