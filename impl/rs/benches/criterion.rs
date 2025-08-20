//! Wall-time benchmarks using criterion.

mod benchmark;
mod helper;

use criterion::criterion_main;

criterion_main! {
    benchmark::dummy::criterion_group,
}
