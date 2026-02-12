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
pub const SCHEMA_VERSION: semver::Version = semver::Version::new(
    capnp::jeff_capnp::SCHEMA_VERSION_MAJOR as u64,
    capnp::jeff_capnp::SCHEMA_VERSION_MINOR as u64,
    capnp::jeff_capnp::SCHEMA_VERSION_PATCH as u64,
);

/// Errors that can occur when processing a jeff file.
#[derive(Debug, Display, From, Error)]
#[non_exhaustive]
pub enum JeffError {
    /// The jeff file is invalid.
    #[display("Invalid jeff file: {_0}")]
    #[from]
    InvalidFile(::capnp::Error),
    /// Invalid schema version.
    #[display("Schema version {v} is too old. Expected {min}")]
    VersionTooOld {
        /// The invalid schema version.
        v: semver::Version,
        /// The minimum compatible version.
        min: String,
    },
    /// The jeff file is too new.
    #[display("Schema version {v} is too new. Expected {max}")]
    VersionTooNew {
        /// The invalid schema version.
        v: semver::Version,
        /// The maximum compatible version.
        max: String,
    },
    /// Error while reading the internal structure.
    #[from]
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
