//! Function definition in a jeff program.
use crate::capnp::jeff_capnp;
use crate::reader::Value;

use super::metadata::sealed::HasMetadataSealed;
use super::string_table::StringTable;
use super::{ReadError, Region, ValueTable};

/// Function index into the module's function table.
pub type FunctionId = u32;

/// Function in a jeff module.
#[derive(Clone, Copy, Debug)]
pub enum Function<'a> {
    /// Function definition with a body.
    Definition(FunctionDefinition<'a>),
    /// Function declaration with only a signature.
    Declaration(FunctionDeclaration<'a>),
}

/// Function definition in a jeff module.
#[derive(Clone, Copy, Debug)]
pub struct FunctionDefinition<'a> {
    /// Internal capnproto function definition.
    function: jeff_capnp::function::Reader<'a>,
    /// Reader for the function's body.
    body: jeff_capnp::region::Reader<'a>,
    /// Function-level register of typed hyperedges.
    values: ValueTable<'a>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
}

/// Function declaration in a jeff module.
#[derive(Clone, Copy, Debug)]
pub struct FunctionDeclaration<'a> {
    /// Internal capnproto function declaration.
    function: jeff_capnp::function::Reader<'a>,
    /// Reader for the function's inputs.
    inputs: capnp::struct_list::Reader<'a, jeff_capnp::value::Owned>,
    /// Reader for the function's outputs.
    outputs: capnp::struct_list::Reader<'a, jeff_capnp::value::Owned>,
    /// Module-level register of reused strings.
    strings: StringTable<'a>,
}

impl<'a> Function<'a> {
    /// Create a new function view from a capnp reader.
    pub(crate) fn read_capnp(
        function: jeff_capnp::function::Reader<'a>,
        strings: StringTable<'a>,
    ) -> Self {
        match function.which().expect("Function should be valid") {
            jeff_capnp::function::Which::Definition(def) => {
                let body = def.get_body().expect("Body should be present");
                let values = ValueTable::read_capnp(
                    def.get_values().expect("Values should be present"),
                    strings,
                );
                let def = FunctionDefinition {
                    function,
                    body,
                    values,
                    strings,
                };
                Self::Definition(def)
            }
            jeff_capnp::function::Which::Declaration(decl) => {
                let inputs = decl.get_inputs().expect("Inputs should be present");
                let outputs = decl.get_outputs().expect("Outputs should be present");
                let decl = FunctionDeclaration {
                    function,
                    inputs,
                    outputs,
                    strings,
                };
                Self::Declaration(decl)
            }
        }
    }

    /// Returns the name of this function.
    ///
    /// # Panics
    ///
    /// Panics if the function name index is out of bounds or not valid utf8.
    pub fn name(&self) -> &str {
        match self {
            Function::Declaration(decl) => decl.name(),
            Function::Definition(def) => def.name(),
        }
    }

    /// Returns the input types of this function.
    pub fn input_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + '_ {
        match self {
            Function::Declaration(decl) => itertools::Either::Left(decl.input_types()),
            Function::Definition(def) => itertools::Either::Right(def.input_types()),
        }
    }

    /// Returns the output types of this function.
    pub fn output_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + '_ {
        match self {
            Function::Declaration(decl) => itertools::Either::Left(decl.output_types()),
            Function::Definition(def) => itertools::Either::Right(def.output_types()),
        }
    }
}

impl<'a> FunctionDefinition<'a> {
    /// Returns the name of this function.
    ///
    /// # Panics
    ///
    /// Panics if the function name index is out of bounds or not valid utf8.
    pub fn name(&self) -> &str {
        self.strings
            .get(self.function.get_name(), "function name")
            .expect("Invalid function name definition")
    }

    /// Returns the dataflow region associated with this function.
    pub fn body(&self) -> Region<'a> {
        Region::read_capnp(self.body, self.strings, self.values())
    }

    /// Returns the value table associated with this function.
    pub fn values(&self) -> ValueTable<'a> {
        self.values
    }

    /// Returns the input types of this function.
    pub fn input_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + 'a {
        self.body().sources()
    }

    /// Returns the output types of this function.
    pub fn output_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + 'a {
        self.body().targets()
    }
}

impl<'a> FunctionDeclaration<'a> {
    /// Returns the name of this function.
    ///
    /// # Panics
    ///
    /// Panics if the function name index is out of bounds or not valid utf8.
    pub fn name(&self) -> &str {
        self.strings
            .get(self.function.get_name(), "function name")
            .expect("Invalid function name definition")
    }

    /// Returns the input types of this function.
    pub fn input_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + '_ {
        self.inputs
            .iter()
            .map(move |value| Ok(Value::read_capnp(None, value, self.strings)))
    }

    /// Returns the output types of this function.
    pub fn output_types(&self) -> impl Iterator<Item = Result<Value<'a>, ReadError>> + '_ {
        self.outputs
            .iter()
            .map(move |value| Ok(Value::read_capnp(None, value, self.strings)))
    }
}

impl<'a> HasMetadataSealed for Function<'a> {
    fn strings(&self) -> StringTable<'a> {
        match self {
            Function::Declaration(decl) => decl.strings,
            Function::Definition(def) => def.strings,
        }
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'_, jeff_capnp::meta::Owned> {
        match self {
            Function::Declaration(decl) => decl.metadata_reader(),
            Function::Definition(def) => def.metadata_reader(),
        }
    }
}

impl<'a> HasMetadataSealed for FunctionDeclaration<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'_, jeff_capnp::meta::Owned> {
        self.function
            .get_metadata()
            .expect("Metadata should be present")
    }
}

impl<'a> HasMetadataSealed for FunctionDefinition<'a> {
    fn strings(&self) -> StringTable<'a> {
        self.strings
    }

    fn metadata_reader(&self) -> capnp::struct_list::Reader<'_, jeff_capnp::meta::Owned> {
        self.function
            .get_metadata()
            .expect("Metadata should be present")
    }
}
