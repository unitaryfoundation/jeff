#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load_positive(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/positive")
        .join(name);
    let file = File::open(&path).unwrap_or_else(|_| panic!("missing fixture: {path:?}"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn load_example(rel: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../examples")
        .join(rel);
    let file = File::open(&path).unwrap_or_else(|_| panic!("missing example: {path:?}"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

// positive tests

#[test]
fn valid_alloc_gate_measure() {
    let errors = load_positive("valid_alloc_gate_measure.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_deep_qubit_chain() {
    let errors = load_positive("valid_deep_qubit_chain.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_for_qubit_isolation() {
    let errors = load_positive("valid_for_qubit_isolation.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_int_float_ops() {
    let errors = load_positive("valid_int_float_ops.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_while_isolation() {
    let errors = load_positive("valid_while_isolation.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn valid_three_qubit_gates() {
    let errors = load_positive("valid_three_qubit_gates.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

// examples
#[test]
fn example_qubits() {
    let errors = load_example("qubits/qubits.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn example_entangled_qs() {
    let errors = load_example("entangled_qs/entangled_qs.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn example_entangled_calls() {
    let errors = load_example("entangled_calls/entangled_calls.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn example_catalyst_simple() {
    let errors = load_example("catalyst_simple/catalyst_simple.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn example_catalyst_tket_opt() {
    let errors = load_example("catalyst_tket_opt/catalyst_tket_opt.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}

#[test]
fn example_python_optimization() {
    let errors = load_example("python_optimization/python_optimization.jeff");
    assert!(errors.is_empty(), "expected no errors, got: {errors:?}");
}
