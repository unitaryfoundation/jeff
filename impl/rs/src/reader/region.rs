//! Dataflow region definition in a jeff program.
use crate::capnp::jeff_capnp;
use crate::reader::value::{ValueTable, WireValue};
use crate::Direction;

use super::metadata::sealed::HasMetadataSealed;
use super::op::Operation;
use super::string_table::StringTable;
use super::value::ValueId;
use super::ReadError;

/// Dataflow region defined in a jeff module.
#[derive(Clone, Copy, Debug)]
pub struct Region<'a> {
    /// Internal capnproto region definition.
    region: jeff_capnp::region::Reader<'a>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
    /// Function-level register of typed hyperedges.
    values: ValueTable<'a>,
}

impl<'a> Region<'a> {
    /// Create a new dataflow region reader from a capnp reader.
    pub(crate) fn read_capnp(
        region: jeff_capnp::region::Reader<'a>,
        strings: StringTable<'a>,
        values: ValueTable<'a>,
    ) -> Self {
        Self {
            region,
            strings,
            values,
        }
    }

    /// Returns an iterator over the sources or target values of this region.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if an encoded value references an invalid index in the value table.
    pub fn boundary(
        &self,
        direction: Direction,
    ) -> impl Iterator<Item = Result<WireValue<'a>, ReadError>> {
        let value_table = self.values;
        let values = match direction {
            Direction::Incoming => self.region.get_sources(),
            Direction::Outgoing => self.region.get_targets(),
        }
        .expect("Boundary should be present");
        values.iter().map(move |idx| value_table.get(idx))
    }

    /// Return an iterator over the source values of this region.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if an encoded value references an invalid index in the value table.
    pub fn sources(&self) -> impl Iterator<Item = Result<WireValue<'a>, ReadError>> {
        self.boundary(Direction::Incoming)
    }

    /// Return an iterator over the target values of this region.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if an encoded value references an invalid index in the value table.
    pub fn targets(&self) -> impl Iterator<Item = Result<WireValue<'a>, ReadError>> {
        self.boundary(Direction::Outgoing)
    }

    /// Returns the number of sources or target values in this region.
    pub fn boundary_count(&self, direction: Direction) -> usize {
        match direction {
            Direction::Incoming => self.region.get_sources(),
            Direction::Outgoing => self.region.get_targets(),
        }
        .expect("Boundary should be present")
        .len() as usize
    }

    /// Returns the number of source values in this region.
    pub fn source_count(&self) -> usize {
        self.boundary_count(Direction::Incoming)
    }

    /// Returns the number of target values in this region.
    pub fn target_count(&self) -> usize {
        self.boundary_count(Direction::Outgoing)
    }

    /// Returns the boundary value at the given index, or `None` if the index is
    /// out of bounds.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the encoded value references an invalid index in the value table.
    pub fn boundary_value(
        &self,
        direction: Direction,
        idx: usize,
    ) -> Option<Result<WireValue<'a>, ReadError>> {
        let values = match direction {
            Direction::Incoming => self.region.get_sources(),
            Direction::Outgoing => self.region.get_targets(),
        }
        .expect("Boundary should be present");
        if idx >= values.len() as usize {
            return None;
        }
        Some(self.values.get(values.get(idx as ValueId)))
    }

    /// Returns the source value at the given index, or `None` if the index is
    /// out of bounds.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the encoded value references an invalid index in the value table.
    pub fn source(&self, idx: usize) -> Option<Result<WireValue<'a>, ReadError>> {
        self.boundary_value(Direction::Incoming, idx)
    }

    /// Returns the target value at the given index, or `None` if the index is
    /// out of bounds.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the encoded value references an invalid index in the value table.
    pub fn target(&self, idx: usize) -> Option<Result<WireValue<'a>, ReadError>> {
        self.boundary_value(Direction::Outgoing, idx)
    }

    /// Returns an iterator over the operations in this region.
    pub fn operations(&self) -> impl Iterator<Item = Operation<'a>> {
        let strings_table = self.strings;
        let value_table = self.values;
        self.region
            .get_operations()
            .expect("Ops should be present")
            .iter()
            .map(move |op| Operation::read_capnp(op, strings_table, value_table))
    }

    /// Returns the number of operations in this region.
    pub fn operation_count(&self) -> usize {
        self.region
            .get_operations()
            .expect("Ops should be present")
            .len() as usize
    }

    /// Returns the `n`-th operation in this region.
    ///
    /// # Panics
    ///
    /// Panics if `n` is equal or greater than [`Region::operation_count`].
    pub fn operation(&self, n: usize) -> Operation<'a> {
        Operation::read_capnp(
            self.region
                .get_operations()
                .expect("Ops should be present")
                .get(n as u32),
            self.strings,
            self.values,
        )
    }
}

impl<'a> HasMetadataSealed for Region<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.region
            .get_metadata()
            .expect("Metadata should be present")
    }
}
