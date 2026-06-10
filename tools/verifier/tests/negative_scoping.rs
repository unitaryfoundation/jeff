#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/scoping")
        .join(name);
    let file = File::open(&path)
        .unwrap_or_else(|_| panic!("missing fixture: {path:?} — run generate_test_cases.py first"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn has_isolation(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::IsolationViolation { .. }))
}

#[test]
fn for_body_captures_outer() {
    assert!(has_isolation(&load("for_captures_outer.jeff")));
}

#[test]
fn while_condition_captures_outer() {
    assert!(has_isolation(&load("while_cond_captures_outer.jeff")));
}

#[test]
fn while_body_captures_outer() {
    assert!(has_isolation(&load("while_body_captures_outer.jeff")));
}

#[test]
fn dowhile_body_captures_outer() {
    assert!(has_isolation(&load("dowhile_body_captures_outer.jeff")));
}

#[test]
fn dowhile_condition_captures_outer() {
    assert!(has_isolation(&load("dowhile_cond_captures_outer.jeff")));
}

#[test]
fn switch_branch_captures_outer() {
    assert!(has_isolation(&load("switch_captures_outer.jeff")));
}

#[test]
fn nested_for_captures_grandparent() {
    assert!(has_isolation(&load("nested_captures_grandparent.jeff")));
}
