#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/module")
        .join(name);
    let file = File::open(&path)
        .unwrap_or_else(|_| panic!("missing fixture: {path:?} — run generate_test_cases.py first"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

#[test]
fn missing_version() {
    let errors = load("missing_version.jeff");
    assert!(
        errors.contains(&VerificationError::MissingVersion),
        "expected MissingVersion, got: {errors:?}"
    );
}

#[test]
fn entrypoint_oob() {
    let errors = load("entrypoint_oob.jeff");
    assert!(
        errors.contains(&VerificationError::InvalidEntrypoint),
        "expected InvalidEntrypoint, got: {errors:?}"
    );
}

#[test]
fn no_functions_gives_both_errors() {
    let errors = load("no_functions.jeff");
    assert!(
        errors.contains(&VerificationError::MissingVersion),
        "expected MissingVersion in {errors:?}"
    );
    assert!(
        errors.contains(&VerificationError::InvalidEntrypoint),
        "expected InvalidEntrypoint in {errors:?}"
    );
}
