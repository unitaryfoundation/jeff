//! The data model of the jeff representation.
//!
//! This crate defines data structures for zero-copy decoding of jeff files.
mod capnp;
mod jeff;

#[cfg(test)]
mod test;

pub mod reader;
pub mod types;
pub use jeff::Jeff;

// The capnp-generated code is re-exported here, but in general it should not be
// used directly.
//
// No semver guarantees are provided for this module.
#[doc(hidden)]
pub use capnp::jeff_capnp;

use derive_more::derive::{Display, Error, From};

/// Latest version of the jeff schema.
pub const SCHEMA_VERSION: u32 = 0;

/// Errors that can occur when processing a jeff file.
#[derive(Debug, Display, From, Error)]
#[non_exhaustive]
pub enum JeffError {
    /// The jeff file is invalid.
    #[display("Invalid jeff file: {_0}")]
    InvalidFile(::capnp::Error),
    /// Invalid schema version.
    #[display("Invalid schema version: {v}. Expected {}", Jeff::VERSION)]
    InvalidVersion {
        /// The invalid schema version.
        v: u32,
    },
    /// Error while reading the internal structure.
    ReadError(reader::ReadError),
}

/// Direction of a port.
#[derive(Clone, Copy, Debug, Display, PartialEq, PartialOrd, Eq, Ord, Hash, Default)]
pub enum Direction {
    /// Input to a node.
    #[default]
    Incoming = 0,
    /// Output from a node.
    Outgoing = 1,
}

impl Direction {
    /// Incoming and outgoing directions.
    pub const BOTH: [Direction; 2] = [Direction::Incoming, Direction::Outgoing];

    /// Returns the opposite direction.
    #[inline(always)]
    pub fn reverse(self) -> Direction {
        match self {
            Direction::Incoming => Direction::Outgoing,
            Direction::Outgoing => Direction::Incoming,
        }
    }
}
