//! Integration tests for the jeff-verify binary.

use std::path::PathBuf;
use std::process::Command;

const FIXTURES_DIR: &str = "tests/fixtures";

fn run_verifier(fixture_path: &str) -> (bool, String) {
    let output = Command::new(env!("CARGO_BIN_EXE_jeff-verify"))
        .arg(fixture_path)
        .output()
        .expect("Failed to run verifier");

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = if stderr.is_empty() {
        stdout
    } else {
        format!("{stdout}\n{stderr}")
    };

    (output.status.success(), combined)
}

fn fixture_path(name: &str) -> String {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join(FIXTURES_DIR)
        .join(format!("{name}.jeff"));
    path.to_str()
        .expect("Path should be valid UTF-8")
        .to_string()
}

#[test]
fn valid_simple_qubits() {
    // Uses existing example from ../../examples/qubits/qubits.jeff
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let path = base.join("../../examples/qubits/qubits.jeff");
    let (ok, output) = run_verifier(path.to_str().unwrap());
    assert!(ok, "Valid qubits example should pass all checks.\n{output}");
}

#[test]
fn valid_entangled_qs() {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let path = base.join("../../examples/entangled_qs/entangled_qs.jeff");
    let (ok, output) = run_verifier(path.to_str().unwrap());
    assert!(
        ok,
        "Valid entangled_qs example should pass all checks.\n{output}"
    );
}

#[test]
fn valid_entangled_calls() {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let path = base.join("../../examples/entangled_calls/entangled_calls.jeff");
    let (ok, output) = run_verifier(path.to_str().unwrap());
    assert!(
        ok,
        "Valid entangled_calls example should pass all checks.\n{output}"
    );
}

#[test]
fn invalid_bad_entrypoint() {
    let path = fixture_path("invalid/bad_entrypoint");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "bad_entrypoint should fail.\n{output}");
    assert!(
        output.contains("[attributes]"),
        "Should report attribute error.\n{output}"
    );
}

#[test]
fn invalid_use_before_def() {
    let path = fixture_path("invalid/use_before_def");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "use_before_def should fail.\n{output}");
    assert!(
        output.contains("[ssa]"),
        "Should report SSA error.\n{output}"
    );
}

#[test]
fn invalid_type_mismatch() {
    let path = fixture_path("invalid/type_mismatch");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "type_mismatch should fail.\n{output}");
    assert!(
        output.contains("[types]"),
        "Should report type error.\n{output}"
    );
}

#[test]
fn invalid_non_linear_qubit() {
    let path = fixture_path("invalid/non_linear_qubit");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "non_linear_qubit should fail.\n{output}");
    assert!(
        output.contains("[linearity]"),
        "Should report linearity error.\n{output}"
    );
}

#[test]
fn invalid_int_bitwidth() {
    let path = fixture_path("invalid/int_bitwidth");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "int_bitwidth should fail.\n{output}");
    assert!(
        output.contains("[types]"),
        "Should report type error.\n{output}"
    );
    assert!(
        output.contains("bitwidth"),
        "Should mention bitwidth mismatch.\n{output}"
    );
}

#[test]
fn invalid_float_precision() {
    let path = fixture_path("invalid/float_precision");
    let (ok, output) = run_verifier(&path);
    assert!(!ok, "float_precision should fail.\n{output}");
    assert!(
        output.contains("[types]"),
        "Should report type error.\n{output}"
    );
    assert!(
        output.contains("precision"),
        "Should mention precision mismatch.\n{output}"
    );
}
