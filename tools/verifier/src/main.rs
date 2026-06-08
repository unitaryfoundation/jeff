//! Verification tool for jeff programs.
//!
//! Checks a jeff file for common issues including:
//! - Required module attributes (entrypoint)
//! - SSA validity (all values defined before use)
//! - Type consistency for operations
//! - Qubit linearity (qubits consumed at most once)
//! - Region isolation (nested regions don't bypass boundaries)

mod checks;

use clap::Parser;
use jeff::reader::ReadJeff;
use jeff::Jeff;
use std::path::PathBuf;
use std::process;

#[derive(Parser)]
#[command(name = "jeff-verify")]
#[command(about = "Verification tool for jeff programs")]
struct Cli {
    /// Path to the jeff file to verify
    path: PathBuf,
}

fn main() {
    let cli = Cli::parse();

    let file = match std::fs::File::open(&cli.path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("Error: could not open '{}': {e}", cli.path.display());
            process::exit(1);
        }
    };

    let jeff = match Jeff::read(file) {
        Ok(j) => j,
        Err(e) => {
            eprintln!("Error: could not read jeff file: {e}");
            process::exit(1);
        }
    };

    let module = jeff.module();
    let errors = checks::run_all(&module);

    if errors.is_empty() {
        println!("All checks passed.");
    } else {
        for err in &errors {
            println!("FAIL: {err}");
        }
        process::exit(1);
    }
}
