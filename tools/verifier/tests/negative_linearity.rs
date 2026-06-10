#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/linearity")
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
fn qubit_produced_twice() {
    let errors = load("qubit_produced_twice.jeff");
    assert!(
        errors.iter().any(|e| matches!(
            e,
            VerificationError::LinearValueProducedMultipleTimes { .. }
        )),
        "expected LinearValueProducedMultipleTimes, got: {errors:?}"
    );
}

#[test]
fn qubit_consumed_twice() {
    let errors = load("qubit_consumed_twice.jeff");
    assert!(
        errors.iter().any(|e| matches!(
            e,
            VerificationError::LinearValueConsumedMultipleTimes { .. }
        )),
        "expected LinearValueConsumedMultipleTimes, got: {errors:?}"
    );
}

#[test]
fn qubit_never_consumed() {
    let errors = load("qubit_never_consumed.jeff");
    assert!(
        errors
            .iter()
            .any(|e| matches!(e, VerificationError::LinearValueNeverConsumed { .. })),
        "expected LinearValueNeverConsumed, got: {errors:?}"
    );
}
