#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/types")
        .join(name);
    let file = File::open(&path)
        .unwrap_or_else(|_| panic!("missing fixture: {path:?} — run generate_test_cases.py first"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn has_mismatch(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::TypeMismatch { .. }))
}

fn has_bad_input(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::InvalidInputType { .. }))
}

fn has_bad_output(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::InvalidOutputType { .. }))
}

// ── int ──────────────────────────────────────

#[test]
fn int_add_mixed_bitwidths() {
    assert!(has_mismatch(&load("int_add_mixed_bitwidths.jeff")));
}

#[test]
fn int_compare_mixed_bitwidths() {
    assert!(has_mismatch(&load("int_compare_mixed_bitwidths.jeff")));
}

#[test]
fn int_compare_bad_output_type() {
    assert!(has_bad_output(&load("int_compare_bad_output.jeff")));
}

#[test]
fn int_unary_output_type_mismatch() {
    assert!(has_mismatch(&load("int_unary_bad_output.jeff")));
}

// ── float ────────────────────────────────────

#[test]
fn float_add_mixed_precisions() {
    assert!(has_mismatch(&load("float_add_mixed_precisions.jeff")));
}

#[test]
fn float_compare_mixed_precisions() {
    assert!(has_mismatch(&load("float_compare_mixed_precisions.jeff")));
}

#[test]
fn float_compare_bad_output_type() {
    assert!(has_bad_output(&load("float_compare_bad_output.jeff")));
}

// ── qubit ────────────────────────────────────

#[test]
fn alloc_bad_output_type() {
    assert!(has_bad_output(&load("alloc_bad_output.jeff")));
}

#[test]
fn measure_bad_input_type() {
    assert!(has_bad_input(&load("measure_bad_input.jeff")));
}

#[test]
fn measure_bad_output_type() {
    assert!(has_bad_output(&load("measure_bad_output.jeff")));
}

#[test]
fn measurend_bad_first_output() {
    assert!(has_bad_output(&load("measurend_bad_first_output.jeff")));
}

#[test]
fn measurend_bad_second_output() {
    assert!(has_bad_output(&load("measurend_bad_second_output.jeff")));
}

#[test]
fn free_bad_input_type() {
    assert!(has_bad_input(&load("free_bad_input.jeff")));
}

#[test]
fn gate_non_qubit_input() {
    assert!(has_bad_input(&load("gate_bad_qubit_input.jeff")));
}

#[test]
fn gate_non_qubit_output() {
    assert!(has_bad_output(&load("gate_bad_qubit_output.jeff")));
}

#[test]
fn gate_non_float_param() {
    assert!(has_bad_input(&load("gate_bad_param_type.jeff")));
}

// ── qubit alloc / free / reset ────────────────

#[test]
fn alloc_has_unexpected_input() {
    assert!(has_bad_input(&load("alloc_unexpected_input.jeff")));
}

#[test]
fn free_has_unexpected_output() {
    assert!(has_bad_output(&load("free_unexpected_output.jeff")));
}

// ── gate arity ────────────────────────────────

fn has_wrong_arity(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::WrongArity { .. }))
}

#[test]
fn gate_too_few_qubit_inputs() {
    assert!(has_wrong_arity(&load("gate_too_few_qubit_inputs.jeff")));
}

#[test]
fn gate_wrong_output_count() {
    assert!(has_wrong_arity(&load("gate_wrong_output_count.jeff")));
}

#[test]
fn gate_missing_param_input() {
    assert!(has_wrong_arity(&load("gate_missing_param_input.jeff")));
}

// ── qureg ops ────────────────────────────────

#[test]
fn qureg_alloc_bad_input_type() {
    assert!(has_bad_input(&load("qureg_alloc_bad_input.jeff")));
}

#[test]
fn qureg_alloc_bad_output_type() {
    assert!(has_bad_output(&load("qureg_alloc_bad_output.jeff")));
}

#[test]
fn qureg_free_bad_input_type() {
    assert!(has_bad_input(&load("qureg_free_bad_input.jeff")));
}

#[test]
fn qureg_extract_index_bad_reg_input() {
    assert!(has_bad_input(&load(
        "qureg_extract_index_bad_reg_input.jeff"
    )));
}

#[test]
fn qureg_extract_index_bad_idx_input() {
    assert!(has_bad_input(&load(
        "qureg_extract_index_bad_idx_input.jeff"
    )));
}

#[test]
fn qureg_extract_index_bad_qubit_output() {
    assert!(has_bad_output(&load(
        "qureg_extract_index_bad_qubit_output.jeff"
    )));
}

#[test]
fn qureg_insert_index_bad_qubit_input() {
    assert!(has_bad_input(&load(
        "qureg_insert_index_bad_qubit_input.jeff"
    )));
}

#[test]
fn qureg_length_bad_output_type() {
    assert!(has_bad_output(&load("qureg_length_bad_output.jeff")));
}

#[test]
fn qureg_join_bad_input_type() {
    assert!(has_bad_input(&load("qureg_join_bad_input.jeff")));
}
