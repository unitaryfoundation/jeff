#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load_negative(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative")
        .join(name);
    let file = File::open(&path).unwrap_or_else(|_| panic!("missing fixture: {path:?}"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

#[test]
fn missing_version() {
    let errors = load_negative("missing_version.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::MissingVersion)),
        "expected MissingVersion, got: {errors:?}"
    );
}

#[test]
fn incompatible_version() {
    let errors = load_negative("incompatible_version.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::IncompatibleVersion)),
        "expected IncompatibleVersion, got: {errors:?}"
    );
}

#[test]
fn invalid_entrypoint() {
    let errors = load_negative("invalid_entrypoint.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::InvalidEntrypoint)),
        "expected InvalidEntrypoint, got: {errors:?}"
    );
}

#[test]
fn value_out_of_bounds() {
    let errors = load_negative("value_out_of_bounds.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::ValueOutOfBounds { .. })),
        "expected ValueOutOfBounds, got: {errors:?}"
    );
}

#[test]
fn used_before_defined() {
    let errors = load_negative("used_before_defined.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::UsedBeforeDefined { .. })),
        "expected UsedBeforeDefined, got: {errors:?}"
    );
}

#[test]
fn value_produced_twice() {
    let errors = load_negative("value_produced_twice.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::ValueProducedMultipleTimes { .. })),
        "expected ValueProducedMultipleTimes, got: {errors:?}"
    );
}

#[test]
fn linear_never_consumed() {
    let errors = load_negative("linear_never_consumed.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::LinearValueNeverConsumed { .. })),
        "expected LinearValueNeverConsumed, got: {errors:?}"
    );
}

#[test]
fn linear_consumed_twice() {
    let errors = load_negative("linear_consumed_twice.jeff");
    assert!(
        errors.iter().any(|e| matches!(
            e,
            VerificationError::LinearValueConsumedMultipleTimes { .. }
        )),
        "expected LinearValueConsumedMultipleTimes, got: {errors:?}"
    );
}

#[test]
fn type_mismatch() {
    let errors = load_negative("type_mismatch.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::TypeMismatch { .. })),
        "expected TypeMismatch, got: {errors:?}"
    );
}

#[test]
fn invalid_input_type() {
    let errors = load_negative("invalid_input_type.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::InvalidInputType { .. })),
        "expected InvalidInputType, got: {errors:?}"
    );
}

#[test]
fn invalid_output_type() {
    let errors = load_negative("invalid_output_type.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::InvalidOutputType { .. })),
        "expected InvalidOutputType, got: {errors:?}"
    );
}

#[test]
fn wrong_arity() {
    let errors = load_negative("wrong_arity.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::WrongArity { .. })),
        "expected WrongArity, got: {errors:?}"
    );
}

#[test]
fn isolation_violation() {
    let errors = load_negative("isolation_violation.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::IsolationViolation { .. })),
        "expected IsolationViolation, got: {errors:?}"
    );
}
