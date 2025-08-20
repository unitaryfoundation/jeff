use criterion::{criterion_group, Criterion};

use crate::helper::*;

// -----------------------------------------------------------------------------
// Benchmark functions
// -----------------------------------------------------------------------------

struct Dummy {
    size: usize,
}
impl SizedBenchmark for Dummy {
    fn name() -> &'static str {
        "dummy"
    }

    fn setup(size: usize) -> Self {
        Self { size }
    }

    fn run(&self) -> impl Sized {
        // Sleep for some time
        std::thread::sleep(std::time::Duration::from_nanos(self.size as u64));
    }
}

// -----------------------------------------------------------------------------
// iai_callgrind definitions
// -----------------------------------------------------------------------------

sized_iai_benchmark!(callgrind_dummy, Dummy);

iai_callgrind::library_benchmark_group!(
    name = callgrind_group;
    benchmarks =
        callgrind_dummy,
);

// -----------------------------------------------------------------------------
// Criterion definitions
// -----------------------------------------------------------------------------

criterion_group! {
    name = criterion_group;
    config = Criterion::default();
    targets =
        Dummy::criterion,
}
