//! View of jeff data.
//!
//! Programs are composed of a top-level [`Module`] that contains a list of [`Function`]s.

mod function;
mod metadata;
mod module;
mod op;
mod region;
mod string_table;
mod value;

pub mod optype;

pub use function::{Function, FunctionId};
pub use metadata::{HasMetadata, Metadata};
pub use module::Module;
pub use op::Operation;
pub use region::Region;
pub use value::{Value, ValueId, ValueTable};

use derive_more::derive::{Display, Error, From};

/// Structure that can return a read-only view of a jeff file.
pub trait ReadJeff {
    /// Returns a read-only reference to the capnp jeff module.
    fn module(&self) -> Module<'_>;
}

/// Errors that can occur when accessing a jeff program.
#[derive(Debug, Display, From, Error)]
#[non_exhaustive]
pub enum ReadError {
    /// String index into the module's string table was out of bounds.
    #[display("{context} string value has index {idx}, but only {count} entries are available")]
    StringOutOfBounds {
        /// The context in which the error occurred.
        context: &'static str,
        /// The requested index into the module's `strings`.
        idx: u32,
        /// The total number of entries in the module's `strings`.
        count: usize,
    },
    /// The encoded string had a non-utf8 name.
    #[display("{context} string value with index {idx} was not valid utf8.")]
    StringNotUtf8 {
        /// The context in which the error occurred.
        context: &'static str,
        /// The index of the metadata name.
        idx: u32,
        /// The utf8 error
        source: core::str::Utf8Error,
    },
    /// Value index into the function's value table was out of bounds.
    #[display("Function value has index {idx}, but only {count} entries are available")]
    ValueOutOfBounds {
        /// The requested index into the function values.
        idx: u32,
        /// The total number of entries in the function values.
        count: usize,
    },
}
