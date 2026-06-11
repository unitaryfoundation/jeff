//! Checks for required module-level attributes.

use jeff::reader::{Function, Module};

use crate::VerificationError;

/// Verify that the module has a valid entrypoint.
pub fn verify_module_attributes(module: Module<'_>, errors: &mut Vec<VerificationError>) {
    match module.try_function(module.entrypoint_id()) {
        None | Some(Function::Declaration(_)) => {
            errors.push(VerificationError::InvalidEntrypoint);
        }
        Some(Function::Definition(_)) => {}
    }
}
