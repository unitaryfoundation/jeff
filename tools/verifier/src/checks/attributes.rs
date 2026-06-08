use jeff::reader::Module;

use super::{Check, CheckError};

pub struct AttributesCheck;

impl Check for AttributesCheck {
    fn name(&self) -> &'static str {
        "attributes"
    }

    fn check(&self, module: &Module<'_>) -> Vec<CheckError> {
        let mut errors = vec![];

        let entry_id = module.entrypoint_id() as usize;
        let func_count = module.function_count();

        if entry_id == 0 && func_count > 0 {
            errors.push(CheckError {
                check_name: self.name(),
                message: format!(
                    "Entrypoint is not specified: module has {func_count} function(s), but entrypoint index is 0 (the default)."
                ),
            });
        } else if entry_id >= func_count {
            errors.push(CheckError {
                check_name: self.name(),
                message: format!(
                    "Entrypoint index {entry_id} is out of bounds: module has {func_count} function(s)."
                ),
            });
        }

        errors
    }
}
