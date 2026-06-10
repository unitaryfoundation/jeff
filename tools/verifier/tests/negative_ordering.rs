#![allow(missing_docs)]
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::{verify_module, VerificationError};

fn load(name: &str) -> Vec<VerificationError> {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/negative/ordering")
        .join(name);
    let file = File::open(&path)
        .unwrap_or_else(|_| panic!("missing fixture: {path:?} — run generate_test_cases.py first"));
    verify_module(
        Jeff::read(file)
            .expect("failed to parse jeff file")
            .module(),
    )
}

fn has_ubd(errors: &[VerificationError]) -> bool {
    errors
        .iter()
        .any(|e| matches!(e, VerificationError::UsedBeforeDefined { .. }))
}

#[test]
fn use_before_define_outer() {
    assert!(has_ubd(&load("use_before_define_outer.jeff")));
}

#[test]
fn use_before_define_for_body() {
    assert!(has_ubd(&load("use_before_define_for.jeff")));
}

#[test]
fn use_before_define_while_condition() {
    assert!(has_ubd(&load("use_before_define_while_cond.jeff")));
}

#[test]
fn use_before_define_while_body() {
    assert!(has_ubd(&load("use_before_define_while_body.jeff")));
}

#[test]
fn use_before_define_dowhile_body() {
    assert!(has_ubd(&load("use_before_define_dowhile_body.jeff")));
}

#[test]
fn use_before_define_dowhile_condition() {
    assert!(has_ubd(&load("use_before_define_dowhile_cond.jeff")));
}

#[test]
fn use_before_define_switch_branch() {
    assert!(has_ubd(&load("use_before_define_switch.jeff")));
}
