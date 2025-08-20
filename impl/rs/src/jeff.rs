//! Current definition of the jeff format.
//!
//! This thin wrapper over the Cap'n Proto-generated code provides a safe
//! interface to load and store jeff files, converting old versions to the
//! current one as needed.

use capnp::message::TypedReader;
use capnp::serialize::{BufferSegments, OwnedSegments};

use crate::capnp::jeff_capnp;
use crate::reader::{Module, ReadJeff};
use crate::JeffError;

/// Copy-on-write representation of jeff programs.
///
/// This thin wrapper over the Cap'n Proto-generated code provides a safe
/// interface to load and store jeff files, converting old versions to the
/// current one as needed.
#[derive(Debug, Clone)]
pub struct Jeff<'a> {
    /// Internal representation of the jeff file.
    module: JeffCow<'a>,
}

/// A [`Cow`]-like enum for jeff programs that may be borrowed from a slice or
/// encoded in an owned buffer.
enum JeffCow<'a> {
    /// A borrowed jeff program.
    Borrowed(TypedReader<BufferSegments<&'a [u8]>, jeff_capnp::module::Owned>),
    /// An owned jeff program.
    Owned(TypedReader<OwnedSegments, jeff_capnp::module::Owned>),
}

impl<'a> Jeff<'a> {
    /// Current version of the jeff format.
    ///
    /// Loading a jeff file with a previous version will automatically upgrade it
    /// to this version.
    pub const VERSION: u32 = crate::SCHEMA_VERSION;

    /// Read a jeff program from a slice without copying the data.
    ///
    /// The data is not copied, but the buffer must outlive the jeff object.
    /// After this call, the slice will be advanced to the end of the jeff data.
    pub fn read_slice(slice: &mut &'a [u8]) -> Result<Self, JeffError> {
        let reader = capnp::serialize::read_message_from_flat_slice(
            slice,
            capnp::message::ReaderOptions::new(),
        )?;
        let module = reader.into_typed::<jeff_capnp::module::Owned>();

        // Ensure the root type is correct.
        module.get()?;

        let slf = Self {
            module: JeffCow::Borrowed(module),
        };
        slf.check_version()?;
        Ok(slf)
    }

    /// Load a jeff program from a reader.
    ///
    /// This will consume the reader and copy the data into an internal buffer.
    /// For a zero-copy version, use [`Jeff::read_slice`].
    ///
    /// For optimal performance, `reader` should be a buffered reader type.
    pub fn read(reader: impl std::io::Read) -> Result<Self, JeffError> {
        let reader = capnp::serialize::read_message(reader, capnp::message::ReaderOptions::new())?;
        let module = reader.into_typed::<jeff_capnp::module::Owned>();

        // Ensure the root type is correct.
        module.get()?;

        let slf = Self {
            module: JeffCow::Owned(module),
        };
        slf.check_version()?;
        Ok(slf)
    }

    /// Check if the schema version is compatible with the current version.
    //
    // TODO: Upgrade older versions to the current one.
    fn check_version(&self) -> Result<(), JeffError> {
        let version = self.module().version();
        match version {
            Self::VERSION => Ok(()),
            _ => Err(JeffError::InvalidVersion { v: version }),
        }
    }
}

impl ReadJeff for Jeff<'_> {
    fn module(&self) -> Module<'_> {
        Module::read_capnp(self.module.module())
    }
}

impl JeffCow<'_> {
    /// Get a reference to the internal jeff module.
    pub fn module(&self) -> jeff_capnp::module::Reader<'_> {
        match self {
            Self::Borrowed(module) => module.get().expect("Root type should be correct"),
            Self::Owned(module) => module.get().expect("Root type should be correct"),
        }
    }
}

impl Clone for JeffCow<'_> {
    fn clone(&self) -> Self {
        todo!()
    }
}

impl std::fmt::Debug for JeffCow<'_> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Borrowed(_) => f.debug_tuple("JeffCow::Borrowed").finish_non_exhaustive(),
            Self::Owned(_) => f.debug_tuple("JeffCow::Owned").finish_non_exhaustive(),
        }
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use crate::test::entangled_qs;
    use rstest::rstest;

    #[rstest]
    fn simple_jeff(entangled_qs: Jeff<'static>) {
        entangled_qs.check_version().unwrap();
    }
}
