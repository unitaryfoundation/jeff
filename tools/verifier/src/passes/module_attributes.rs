//! Checks for required module-level attributes.

use jeff::reader::{Function, Module};

use crate::VerificationError;

/// Verify that the module has a non-zero version and a valid entrypoint.
pub fn verify_module_attributes(module: Module<'_>, errors: &mut Vec<VerificationError>) {
    let v = module.version();
    if v.major == 0 && v.minor == 0 && v.patch == 0 {
        errors.push(VerificationError::MissingVersion);
    }

    match module.try_function(module.entrypoint_id()) {
        None | Some(Function::Declaration(_)) => {
            errors.push(VerificationError::InvalidEntrypoint);
        }
        Some(Function::Definition(_)) => {}
    }
}
