//! Single-shot benchmarks with iai-callgrind.

mod benchmark;
mod helper;

use iai_callgrind::main;

use benchmark::dummy::callgrind_group as dummy;

main!(library_benchmark_groups = dummy,);
