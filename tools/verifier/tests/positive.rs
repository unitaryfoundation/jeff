#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::verify_module;

fn load_positive(name: &str) -> Vec<verifier::VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/positive")
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
fn valid_comprehensive() {
    let errors = load_positive("valid_comprehensive.jeff");
    assert!(
        errors.is_empty(),
        "expected no errors, got:\n{}",
        errors
            .iter()
            .map(|e| format!("  - {e}"))
            .collect::<Vec<_>>()
            .join("\n")
    );
}

#[test]
fn valid_minimal() {
    let errors = load_positive("valid_minimal.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_deeply_nested() {
    let errors = load_positive("valid_deeply_nested.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}
