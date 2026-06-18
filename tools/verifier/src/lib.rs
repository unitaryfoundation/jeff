//! Verifier for jeff quantum program modules.
//!
//! The main entry point is [`verify_module`], which checks a decoded
//! [`jeff::reader::Module`] against all verification passes and returns
//! a list of [`VerificationError`]s.

pub mod analysis;
/// Verification error types and their display messages.
pub mod errors;
pub mod passes;

use jeff::reader::{Function, FunctionDefinition, Module};

pub use errors::VerificationError;

use passes::isolation::verify_isolation;
use passes::module_attributes::verify_module_attributes;
use passes::type_checks::verify_operation_types;
use passes::value_checks::verify_value_checks;

/// Verify a decoded jeff module and return all detected errors.
///
/// Returns an empty [`Vec`] if the module is valid.
/// Returns immediately with a single error if the module version is missing or incompatible,
/// since subsequent passes would produce meaningless results against an unknown schema version.
pub fn verify_module(module: Module<'_>) -> Vec<VerificationError> {
    let v = module.version();
    let s = &jeff::SCHEMA_VERSION;

    if v.major == 0 && v.minor == 0 && v.patch == 0 {
        return vec![VerificationError::MissingVersion];
    }
    if v.major != s.major || v.minor != s.minor || v.patch != s.patch {
        return vec![VerificationError::IncompatibleVersion];
    }

    let mut errors = Vec::new();

    verify_module_attributes(module, &mut errors);

    for function in module.functions() {
        if let Function::Definition(def) = function {
            verify_definition(def, &mut errors);
        }
    }

    errors
}

fn verify_definition(def: FunctionDefinition<'_>, errors: &mut Vec<VerificationError>) {
    verify_value_checks(def, errors);
    verify_operation_types(def.body(), errors);
    verify_isolation(def, errors);
}
