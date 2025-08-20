//! Operations returning a constant value.

use capnp::private::layout::PrimitiveElement;

/// An array of constant values of a primitive type.
#[derive(Clone, Copy)]
pub struct ConstArray<'a, T>
where
    T: PrimitiveElement,
{
    /// The constant values.
    values: capnp::primitive_list::Reader<'a, T>,
}

impl<T: std::fmt::Debug> std::fmt::Debug for ConstArray<'_, T>
where
    T: PrimitiveElement + Copy + capnp::introspect::Introspect,
{
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("ConstArray")
            .field("values", &self.values)
            .finish()
    }
}

impl<'a, T: PrimitiveElement + Copy> ConstArray<'a, T> {
    /// Create a new constant array from a capnp reader.
    pub(crate) fn read_capnp(values: capnp::primitive_list::Reader<'a, T>) -> Self {
        Self { values }
    }

    /// Returns an iterator over the constant values.
    pub fn values(&self) -> impl Iterator<Item = T> + '_ {
        self.values.iter()
    }

    /// Returns the number of constant values.
    pub fn len(&self) -> usize {
        self.values.len() as usize
    }

    /// Returns `true` if the array is empty.
    pub fn is_empty(&self) -> bool {
        self.values.len() == 0
    }

    /// Returns the constant value at the given index.
    ///
    /// # Panics
    ///
    /// Panics if the index is out of bounds.
    pub fn get(&self, idx: usize) -> T {
        self.values.get(idx as u32)
    }
}
