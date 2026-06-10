#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load_bounds(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/bounds")
        .join(name);
    let file = File::open(&path).unwrap_or_else(|_| panic!("missing fixture: {path:?}"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn load_module(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/module")
        .join(name);
    let file = File::open(&path).unwrap_or_else(|_| panic!("missing fixture: {path:?}"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn has_oob(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::ValueOutOfBounds { .. }))
}

#[test]
fn op_input_oob() {
    assert!(has_oob(&load_bounds("op_input_oob.jeff")));
}

#[test]
fn op_output_oob() {
    assert!(has_oob(&load_bounds("op_output_oob.jeff")));
}

#[test]
fn region_source_oob() {
    assert!(has_oob(&load_bounds("region_source_oob.jeff")));
}

#[test]
fn region_target_oob() {
    assert!(has_oob(&load_bounds("region_target_oob.jeff")));
}

#[test]
fn nested_source_oob() {
    assert!(has_oob(&load_bounds("nested_source_oob.jeff")));
}

#[test]
fn nested_target_oob() {
    assert!(has_oob(&load_bounds("nested_target_oob.jeff")));
}

#[test]
fn entrypoint_is_declaration() {
    let errors = load_module("entrypoint_is_declaration.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::InvalidEntrypoint)),
        "expected InvalidEntrypoint, got: {errors:?}"
    );
}
