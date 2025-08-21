//! Node operation definitions.

use crate::reader::value::{ValueTable, WireValue};
use crate::types::Type;
use crate::{jeff_capnp, Direction};

use super::metadata::sealed::HasMetadataSealed;
use super::optype::OpType;
use super::string_table::StringTable;
use super::value::ValueId;
use super::ReadError;

/// Operation in a dataflow graph.
#[derive(Clone, Copy, Debug)]
pub struct Operation<'a> {
    /// Internal capnproto region definition.
    op: jeff_capnp::op::Reader<'a>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
    /// Function-level register of typed hyperedges.
    values: ValueTable<'a>,
}

impl<'a> Operation<'a> {
    /// Create a new dataflow operation reader from a capnp reader.
    pub(crate) fn read_capnp(
        operation: jeff_capnp::op::Reader<'a>,
        strings: StringTable<'a>,
        values: ValueTable<'a>,
    ) -> Self {
        Self {
            op: operation,
            strings,
            values,
        }
    }

    /// Returns the type of this operation.
    pub fn op_type(&self) -> OpType<'a> {
        OpType::read_capnp(self.op.get_instruction(), self.strings, self.values)
    }

    /// Returns an iterator over the input or output values of this operation.
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
            Direction::Incoming => self.op.get_inputs(),
            Direction::Outgoing => self.op.get_outputs(),
        }
        .expect("Boundary should be present");
        values.iter().map(move |idx| value_table.get(idx))
    }

    /// Return an iterator over the input values of this operation.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if an encoded value references an invalid index in the value table.
    pub fn inputs(&self) -> impl Iterator<Item = Result<WireValue<'a>, ReadError>> {
        self.boundary(Direction::Incoming)
    }

    /// Return an iterator over the output values of this operation.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if an encoded value references an invalid index in the value table.
    pub fn outputs(&self) -> impl Iterator<Item = Result<WireValue<'a>, ReadError>> {
        self.boundary(Direction::Outgoing)
    }

    /// Returns the number of inputs or output values in this operation.
    pub fn boundary_count(&self, direction: Direction) -> usize {
        match direction {
            Direction::Incoming => self.op.get_inputs(),
            Direction::Outgoing => self.op.get_outputs(),
        }
        .expect("Boundary should be present")
        .len() as usize
    }

    /// Returns the number of input values in this operation.
    pub fn input_count(&self) -> usize {
        self.boundary_count(Direction::Incoming)
    }

    /// Returns the number of output values in this operation.
    pub fn output_count(&self) -> usize {
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
            Direction::Incoming => self.op.get_inputs(),
            Direction::Outgoing => self.op.get_outputs(),
        }
        .expect("Boundary should be present");
        if idx >= values.len() as usize {
            return None;
        }
        let value_id: ValueId = values.get(idx as u32);
        Some(self.values.get(value_id))
    }

    /// Returns the input value at the given index, or `None` if the index is
    /// out of bounds.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the encoded value references an invalid index in the value table.
    pub fn input(&self, idx: usize) -> Option<Result<WireValue<'a>, ReadError>> {
        self.boundary_value(Direction::Incoming, idx)
    }

    /// Returns the output value at the given index, or `None` if the index is
    /// out of bounds.
    ///
    /// # Errors
    ///
    /// - [`ReadError::ValueOutOfBounds`] if the encoded value references an invalid index in the value table.
    pub fn output(&self, idx: usize) -> Option<Result<WireValue<'a>, ReadError>> {
        self.boundary_value(Direction::Outgoing, idx)
    }

    /// Returns the input types of this function.
    pub fn input_types(&self) -> impl Iterator<Item = Result<Type, ReadError>> + 'a {
        self.inputs().map(move |res| res.map(|t| t.ty()))
    }

    /// Returns the output types of this function.
    pub fn output_types(&self) -> impl Iterator<Item = Result<Type, ReadError>> + 'a {
        self.outputs().map(move |res| res.map(|t| t.ty()))
    }
}

impl<'a> HasMetadataSealed for Operation<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.op.get_metadata().expect("Metadata should be present")
    }
}
