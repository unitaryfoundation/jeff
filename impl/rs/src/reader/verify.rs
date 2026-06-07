//! Verification helpers for jeff programs.

use std::collections::HashSet;

use derive_more::derive::{Display, Error};

use crate::reader::optype::{ControlFlowOp, OpType};
use crate::reader::value::ValueId;
use crate::reader::{Function, FunctionId, Module, ReadError, ReadJeff, Region};
use crate::SCHEMA_VERSION;

/// A structural verification error found in a jeff program.
#[derive(Debug, Display, Error)]
#[non_exhaustive]
pub enum VerificationError {
    /// The encoded jeff schema version is too old for this reader.
    #[display("Schema version {actual} is too old. Expected at least {expected}")]
    VersionTooOld {
        /// The encoded schema version.
        actual: semver::Version,
        /// The minimum supported schema version.
        expected: semver::Version,
    },
    /// The encoded jeff schema version is too new for this reader.
    #[display("Schema version {actual} is too new. Expected at most {expected}")]
    VersionTooNew {
        /// The encoded schema version.
        actual: semver::Version,
        /// The maximum supported schema version.
        expected: semver::Version,
    },
    /// The module entrypoint points outside the function table.
    #[display("Entrypoint function {entrypoint} is out of bounds for {function_count} functions")]
    InvalidEntrypoint {
        /// The encoded entrypoint function id.
        entrypoint: FunctionId,
        /// The number of functions in the module.
        function_count: usize,
    },
    /// A function call points outside the module function table.
    #[display("Function {function} calls missing function {callee}")]
    InvalidFunctionCall {
        /// The function being verified.
        function: FunctionId,
        /// The missing callee id.
        callee: FunctionId,
    },
    /// A value was consumed before being produced or listed as a region input.
    #[display("Function {function} uses value {value} before it is defined")]
    ValueUsedBeforeDefined {
        /// The function being verified.
        function: FunctionId,
        /// The value id that was used too early.
        value: ValueId,
    },
    /// A region output was not produced in the region.
    #[display("Function {function} returns value {value} before it is defined")]
    UndefinedRegionOutput {
        /// The function being verified.
        function: FunctionId,
        /// The region output value id.
        value: ValueId,
    },
    /// Reading an encoded value failed.
    #[display("Function {function}: {source}")]
    Read {
        /// The function being verified.
        function: FunctionId,
        /// The read error.
        source: ReadError,
    },
}

/// Verify a jeff program and return all structural errors found.
pub fn verify(program: &impl ReadJeff) -> Result<(), Vec<VerificationError>> {
    verify_module(program.module())
}

/// Verify a module view and return all structural errors found.
pub fn verify_module(module: Module<'_>) -> Result<(), Vec<VerificationError>> {
    let mut errors = Vec::new();

    verify_version(module, &mut errors);

    if module.try_function(module.entrypoint_id()).is_none() {
        errors.push(VerificationError::InvalidEntrypoint {
            entrypoint: module.entrypoint_id(),
            function_count: module.function_count(),
        });
    }

    for (function_id, function) in module.functions().enumerate() {
        let function_id = function_id as FunctionId;
        verify_function_signature(function_id, function, &mut errors);
        if let Function::Definition(definition) = function {
            verify_region(
                function_id,
                definition.body(),
                module.function_count(),
                &mut errors,
            );
        }
    }

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors)
    }
}

fn verify_version(module: Module<'_>, errors: &mut Vec<VerificationError>) {
    let version = module.version();
    if version.major < SCHEMA_VERSION.major {
        errors.push(VerificationError::VersionTooOld {
            actual: version,
            expected: SCHEMA_VERSION,
        });
    } else if version.major > SCHEMA_VERSION.major {
        errors.push(VerificationError::VersionTooNew {
            actual: version,
            expected: SCHEMA_VERSION,
        });
    }
}

fn verify_function_signature(
    function_id: FunctionId,
    function: Function<'_>,
    errors: &mut Vec<VerificationError>,
) {
    for input in function.input_types() {
        if let Err(source) = input {
            errors.push(VerificationError::Read {
                function: function_id,
                source,
            });
        }
    }

    for output in function.output_types() {
        if let Err(source) = output {
            errors.push(VerificationError::Read {
                function: function_id,
                source,
            });
        }
    }
}

fn verify_region(
    function_id: FunctionId,
    region: Region<'_>,
    function_count: usize,
    errors: &mut Vec<VerificationError>,
) {
    let mut defined = HashSet::new();

    for source in region.sources() {
        match source {
            Ok(value) => {
                defined.insert(value.id());
            }
            Err(source) => errors.push(VerificationError::Read {
                function: function_id,
                source,
            }),
        }
    }

    for operation in region.operations() {
        for input in operation.inputs() {
            match input {
                Ok(value) if !defined.contains(&value.id()) => {
                    errors.push(VerificationError::ValueUsedBeforeDefined {
                        function: function_id,
                        value: value.id(),
                    });
                }
                Ok(_) => {}
                Err(source) => errors.push(VerificationError::Read {
                    function: function_id,
                    source,
                }),
            }
        }

        verify_nested_regions(function_id, operation.op_type(), function_count, errors);

        for output in operation.outputs() {
            match output {
                Ok(value) => {
                    defined.insert(value.id());
                }
                Err(source) => errors.push(VerificationError::Read {
                    function: function_id,
                    source,
                }),
            }
        }
    }

    for target in region.targets() {
        match target {
            Ok(value) if !defined.contains(&value.id()) => {
                errors.push(VerificationError::UndefinedRegionOutput {
                    function: function_id,
                    value: value.id(),
                });
            }
            Ok(_) => {}
            Err(source) => errors.push(VerificationError::Read {
                function: function_id,
                source,
            }),
        }
    }
}

fn verify_nested_regions(
    function_id: FunctionId,
    op_type: OpType<'_>,
    function_count: usize,
    errors: &mut Vec<VerificationError>,
) {
    match op_type {
        OpType::ControlFlowOp(control_flow) => match *control_flow {
            ControlFlowOp::Switch(switch) => {
                for branch in switch.branches() {
                    verify_region(function_id, branch, function_count, errors);
                }
                if let Some(default) = switch.default_branch() {
                    verify_region(function_id, default, function_count, errors);
                }
            }
            ControlFlowOp::For { region } => {
                verify_region(function_id, region, function_count, errors);
            }
            ControlFlowOp::While { condition, body } => {
                verify_region(function_id, condition, function_count, errors);
                verify_region(function_id, body, function_count, errors);
            }
            ControlFlowOp::DoWhile { body, condition } => {
                verify_region(function_id, body, function_count, errors);
                verify_region(function_id, condition, function_count, errors);
            }
        },
        OpType::FuncOp(func) if usize::from(func.func_idx) >= function_count => {
            errors.push(VerificationError::InvalidFunctionCall {
                function: function_id,
                callee: FunctionId::from(func.func_idx),
            });
        }
        _ => {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::jeff_capnp;

    #[rstest::rstest]
    fn verifies_examples(
        #[values(
            crate::test::qubits(),
            crate::test::entangled_qs(),
            crate::test::entangled_calls()
        )]
        program: crate::Jeff<'static>,
    ) {
        verify(&program).unwrap();
    }

    #[test]
    fn reports_invalid_entrypoint() {
        let mut message = capnp::message::Builder::new_default();
        let mut module_builder = message.init_root::<jeff_capnp::module::Builder>();
        module_builder.set_version(SCHEMA_VERSION.major as u32);
        module_builder.set_version_minor(SCHEMA_VERSION.minor as u32);
        module_builder.set_version_patch(SCHEMA_VERSION.patch as u32);
        module_builder.reborrow().init_functions(0);
        module_builder.reborrow().init_strings(0);
        module_builder.reborrow().init_metadata(0);
        module_builder.set_entrypoint(1);
        let module = Module::read_capnp(module_builder.reborrow_as_reader());

        let errors = verify_module(module).unwrap_err();

        assert!(errors
            .iter()
            .any(|error| matches!(error, VerificationError::InvalidEntrypoint { .. })));
    }
}
