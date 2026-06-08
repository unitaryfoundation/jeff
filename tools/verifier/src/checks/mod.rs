//! Verification checks for jeff programs.

pub mod attributes;
pub mod isolation;
pub mod linearity;
pub mod ssa;
pub mod types;

use jeff::reader::Module;
use std::fmt;

#[derive(Debug)]
pub struct CheckError {
    pub check_name: &'static str,
    pub message: String,
}

impl fmt::Display for CheckError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[{}] {}", self.check_name, self.message)
    }
}

pub trait Check {
    fn name(&self) -> &'static str;
    fn check(&self, module: &Module<'_>) -> Vec<CheckError>;
}

pub fn run_all(module: &Module<'_>) -> Vec<CheckError> {
    let checks: &[&dyn Check] = &[
        &attributes::AttributesCheck,
        &ssa::SsaCheck,
        &types::TypesCheck,
        &linearity::LinearityCheck,
        &isolation::IsolationCheck,
    ];
    let mut errors = vec![];
    for check in checks {
        errors.extend(check.check(module));
    }
    errors
}
