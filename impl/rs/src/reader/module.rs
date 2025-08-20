//! Top-level module definition in a jeff program.
use crate::capnp::jeff_capnp;

use super::function::FunctionId;
use super::metadata::sealed::HasMetadataSealed;
use super::string_table::StringTable;
use super::Function;

/// Top-level module definition in a jeff program.
#[derive(Clone, Copy, Debug)]
pub struct Module<'a> {
    /// Internal capnproto module definition.
    module: jeff_capnp::module::Reader<'a>,
}

impl<'a> Module<'a> {
    /// Create a new module view from a capnp reader.
    pub(crate) fn read_capnp(module: jeff_capnp::module::Reader<'a>) -> Self {
        Self { module }
    }

    /// Version of the jeff protocol used in this module.
    pub fn version(&self) -> u32 {
        self.module.get_version()
    }

    /// Returns the internal reader over the module's functions.
    fn functions_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::function::Owned> {
        self.module
            .get_functions()
            .expect("Functions should be present")
    }

    /// Returns an iterator over the functions defined in this module.
    pub fn functions(&self) -> impl Iterator<Item = Function<'a>> {
        let string_table = self.strings();
        self.functions_reader()
            .iter()
            .map(move |f| Function::read_capnp(f, string_table))
    }

    /// Returns the number of functions defined in this module.
    pub fn function_count(&self) -> usize {
        self.functions_reader().len() as usize
    }

    /// Returns the `n`-th function defined in this module.
    ///
    /// # Panics
    ///
    /// Panics if `n` is equal or greater than [`Module::function_count`].
    pub fn function(&self, n: FunctionId) -> Function<'a> {
        Function::read_capnp(self.functions_reader().get(n), self.strings())
    }

    /// Returns the `n`-th function defined in this module.
    pub fn try_function(&self, n: FunctionId) -> Option<Function<'a>> {
        let f = self.functions_reader().try_get(n)?;
        Some(Function::read_capnp(f, self.strings()))
    }

    /// Returns the internal storage of strings.
    pub fn strings(&self) -> StringTable<'a> {
        StringTable::read_capnp(
            self.module
                .get_strings()
                .expect("Strings should be present"),
        )
    }

    /// Returns the [FunctionId] of the entrypoint function for this module.
    pub fn entrypoint_id(&self) -> FunctionId {
        self.module.get_entrypoint() as FunctionId
    }

    /// Returns the entrypoint function for this module.
    ///
    /// # Panics
    ///
    /// Panics if the entrypoint id in the jeff definition is out of range.
    pub fn entrypoint(&self) -> Function<'a> {
        self.functions().nth(self.entrypoint_id() as usize).unwrap()
    }

    /// Returns the tool name used to generate this program.
    ///
    /// See [`Module::tool_version`].
    pub fn tool(&self) -> &str {
        self.module
            .get_tool()
            .ok()
            .and_then(|r| r.to_str().ok())
            .unwrap_or("")
    }

    /// Returns the tool version used to generate this program.
    ///
    /// See [`Module::tool`].
    pub fn tool_version(&self) -> &str {
        self.module
            .get_tool_version()
            .ok()
            .and_then(|r| r.to_str().ok())
            .unwrap_or("")
    }
}

impl<'a> HasMetadataSealed for Module<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings()
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'a, jeff_capnp::meta::Owned> {
        self.module
            .get_metadata()
            .expect("Metadata should be present")
    }
}
