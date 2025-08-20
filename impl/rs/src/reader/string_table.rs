//! Common string table stored at the module level.

use super::ReadError;

/// A string table stored at the module level.
#[derive(Clone, Copy, Debug)]
pub struct StringTable<'a> {
    /// Internal capnproto string table.
    strings: capnp::text_list::Reader<'a>,
}

impl<'a> StringTable<'a> {
    /// Create a new string table view from a capnp reader.
    pub(crate) fn read_capnp(strings: capnp::text_list::Reader<'a>) -> Self {
        Self { strings }
    }

    /// Returns the string at the given index.
    ///
    /// # Errors
    ///
    /// - [`ReadError::StringOutOfBounds`] if the index is out of bounds.
    /// - [`ReadError::StringNotUtf8`] if the string is not valid utf8.
    pub fn get(&self, idx: u16, access_context: &'static str) -> Result<&'a str, ReadError> {
        let idx = idx as u32;

        let string = self
            .strings
            .try_get(idx)
            .ok_or_else(|| ReadError::StringOutOfBounds {
                context: access_context,
                idx,
                count: self.len(),
            })?
            .expect("Invalid metadata name definition");

        // Decode the string as UTF-8.
        let string = string.to_str().map_err(|e| ReadError::StringNotUtf8 {
            context: access_context,
            idx,
            source: e,
        })?;

        Ok(string)
    }

    /// Returns the number of strings in this table.
    pub fn len(&self) -> usize {
        self.strings.len() as usize
    }
}
