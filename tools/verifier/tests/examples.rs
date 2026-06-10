#![allow(missing_docs)]
//! Run the verifier against every shipped example .jeff file and print the results.
//! This is purely informational — the test always passes.
//! Run with `cargo test -p verifier examples -- --nocapture` to see the output.

use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::fs::File;
use std::path::Path;
use verifier::verify_module;

fn run_example(name: &str) {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../examples")
        .join(name);

    print!("{name}: ");

    let file = match File::open(&path) {
        Ok(f) => f,
        Err(e) => {
            println!("could not open file — {e}");
            return;
        }
    };

    let jeff = match Jeff::read(file) {
        Ok(j) => j,
        Err(e) => {
            println!("read error — {e:?}");
            return;
        }
    };

    let errors = verify_module(jeff.module());
    if errors.is_empty() {
        println!("OK");
    } else {
        println!("{} error(s):", errors.len());
        for e in &errors {
            println!("  - {e}");
        }
    }
}

#[test]
fn verify_examples() {
    println!();
    run_example("qubits/qubits.jeff");
    run_example("entangled_qs/entangled_qs.jeff");
    run_example("entangled_calls/entangled_calls.jeff");
    run_example("catalyst_simple/catalyst_simple.jeff");
    run_example("catalyst_tket_opt/catalyst_tket_opt.jeff");
    run_example("python_optimization/python_optimization.jeff");
}
