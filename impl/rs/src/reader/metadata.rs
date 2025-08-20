//! Metadata associated with jeff elements.

use crate::capnp::jeff_capnp;

use super::string_table::StringTable;
use super::ReadError;

/// A metadata entry, consisting of a name and a value.
#[derive(Clone, Copy)]
pub struct Metadata<'a> {
    /// Internal capnproto function definition.
    name: &'a str,
    /// Value of the metadata entry.
    value: capnp::any_pointer::Reader<'a>,
}

impl<'a> Metadata<'a> {
    /// Create a new function view from a capnp reader.
    ///
    /// # Panics
    ///
    /// Panics if the metadata key string index is out of bounds or not valid utf8.
    pub(crate) fn read_capnp(meta: jeff_capnp::meta::Reader<'a>, strings: StringTable<'a>) -> Self {
        Self::try_read_capnp(meta, strings).unwrap_or_else(|e| panic!("{}", e))
    }

    /// Create a new function view from a capnp reader.
    ///
    /// # Errors
    ///
    /// - [`ReadError::StringOutOfBounds`] if the metadata key string index is out of bounds.
    /// - [`ReadError::StringNotUtf8`] if the metadata key string is not valid utf8.
    pub(crate) fn try_read_capnp(
        meta: jeff_capnp::meta::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Result<Self, ReadError> {
        let name = strings.get(meta.get_name(), "metadata name")?;
        let value = meta.get_value();

        Ok(Self { name, value })
    }

    /// Returns the name of this metadata entry.
    pub fn name(&self) -> &str {
        self.name
    }

    /// Returns the value of this metadata entry, as a capnproto any pointer.
    //
    // TODO: Add `try_value_*` getters that try to cast into str / int / float / etc.
    pub fn value_any_pointer(&self) -> capnp::any_pointer::Reader<'a> {
        self.value
    }

    /// Returns the value as a string.
    ///
    /// Returns `None` if the value cannot be converted to a string.
    pub fn value_str(&self) -> Option<&str> {
        let reader = self.value.get_as::<capnp::text::Reader>().ok()?;
        reader.to_str().ok()
    }
}

impl std::fmt::Debug for Metadata<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Metadata")
            .field("name", &self.name)
            .field("value", &"...")
            .finish()
    }
}

/// Trait for types that have metadata entries.
pub trait HasMetadata: sealed::HasMetadataSealed {
    /// Returns an iterator over the metadata entries for this module.
    fn metadata_entries(&self) -> impl Iterator<Item = Metadata<'_>> {
        self.metadata_reader()
            .iter()
            .map(|m| Metadata::read_capnp(m, self.strings()))
    }

    /// Returns the number of metadata entries in this module.
    fn metadata_count(&self) -> usize {
        self.metadata_reader().len() as usize
    }

    /// Returns the `n`-th metadata entry in this module.
    ///
    /// # Panics
    ///
    /// Panics if `n` is equal or greater than [`HasMetadata::metadata_count`].
    fn metadata(&self, n: usize) -> Metadata<'_> {
        Metadata::read_capnp(self.metadata_reader().get(n as u32), self.strings())
    }

    /// Returns the `n`-th metadata entry in this module.
    ///
    /// Returns `None` if `n` is equal or greater than [`HasMetadata::metadata_count`].
    fn try_metadata(&self, n: usize) -> Option<Metadata<'_>> {
        let m = self.metadata_reader().try_get(n as u32)?;
        Some(Metadata::read_capnp(m, self.strings()))
    }
}

pub(crate) mod sealed {
    use crate::capnp::jeff_capnp;
    use crate::reader::string_table::StringTable;

    pub trait HasMetadataSealed {
        /// Returns the internal storage of strings.
        ///
        /// This is a list of strings that are reused across the different jeff definitions,
        /// and encoded as an index into this list.
        fn strings(&self) -> StringTable<'_>;

        /// Returns the capnproto reader over the element's metadata.
        fn metadata_reader(&self) -> capnp::struct_list::Reader<'_, jeff_capnp::meta::Owned>;
    }
}
