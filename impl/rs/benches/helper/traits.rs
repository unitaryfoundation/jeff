//! Traits to simplify the definition of benchmarks for both criterion and
//! iai_callgrind runners.
#![allow(unused)]

/// A parametric-size benchmark.
pub trait SizedBenchmark: Sized {
    /// Name of the benchmark.
    fn name() -> &'static str;

    /// List of sizes to benchmark.
    fn sizes() -> &'static [usize] {
        &[100, 1_000, 10_000]
    }

    /// Initialize the benchmark with a given problem size.
    ///
    /// Benchmarked sizes default to 100, 1_000, and 10_000 unless overridden.
    fn setup(size: usize) -> Self;

    /// Operation to benchmark.
    ///
    /// Note that the destruction of the return type is measured as part of the benchmark,
    /// so objects with expensive destructors should be avoided.
    fn run(&self) -> impl Sized;

    /// Initialize the benchmark with the smallest size defined in the `sizes` method.
    ///
    /// Used for iai_callgrind benchmarks.
    fn small() -> Self {
        Self::setup(Self::sizes().iter().min().copied().unwrap())
    }

    /// Initialize the benchmark with the biggest size defined in the `sizes` method.
    ///
    /// Used for iai_callgrind benchmarks.
    fn big() -> Self {
        Self::setup(Self::sizes().iter().max().copied().unwrap())
    }

    /// Run the benchmark under criterion for a given list of sizes.
    fn criterion(c: &mut criterion::Criterion) {
        let mut g = c.benchmark_group(Self::name());
        g.plot_config(
            criterion::PlotConfiguration::default()
                .summary_scale(criterion::AxisScale::Logarithmic),
        );

        for &size in Self::sizes() {
            let benchmark = Self::setup(size);
            g.bench_function(criterion::BenchmarkId::new(Self::name(), size), |b| {
                b.iter(|| criterion::black_box(benchmark.run()))
            });
        }
    }
}

/// A parametric-size benchmark that requires some setup between iterations.
pub trait SizedBenchmarkWithInput: Sized {
    /// Type of the prepared state for a single test run.
    type State;

    /// Name of the benchmark.
    fn name() -> &'static str;

    /// List of sizes to benchmark.
    fn sizes() -> &'static [usize] {
        &[100, 1_000, 10_000]
    }

    /// Initialize the benchmark with a given problem size.
    ///
    /// Benchmarked sizes default to 100, 1_000, and 10_000 unless overridden.
    fn setup(size: usize) -> Self;

    /// Prepare the state for a single test run.
    ///
    /// This value will be passed to the `run` method.
    fn prepare_run(&self) -> Self::State;

    /// Operation to benchmark.
    ///
    /// Note that the destruction of the return type is measured as part of the benchmark,
    /// so objects with expensive destructors should be avoided.
    fn run(&self, state: Self::State) -> impl Sized;

    /// Initialize the benchmark with the smallest size defined in the `sizes` method,
    /// and prepare the state for a single test run.
    ///
    /// Used for iai_callgrind benchmarks.
    fn small() -> (Self, Self::State) {
        let size = Self::sizes().iter().min().copied().unwrap();
        let benchmark = Self::setup(size);
        let state = benchmark.prepare_run();
        (benchmark, state)
    }

    /// Initialize the benchmark with the biggest size defined in the `sizes` method,
    /// and prepare the state for a single test run.
    ///
    /// Used for iai_callgrind benchmarks.
    fn big() -> (Self, Self::State) {
        let size = Self::sizes().iter().max().copied().unwrap();
        let benchmark = Self::setup(size);
        let state = benchmark.prepare_run();
        (benchmark, state)
    }

    /// Run the benchmark under criterion for a given list of sizes.
    fn criterion(c: &mut criterion::Criterion) {
        let mut g = c.benchmark_group(Self::name());
        g.plot_config(
            criterion::PlotConfiguration::default()
                .summary_scale(criterion::AxisScale::Logarithmic),
        );

        for &size in Self::sizes() {
            let benchmark = Self::setup(size);
            g.bench_function(criterion::BenchmarkId::new(Self::name(), size), |b| {
                b.iter_batched(
                    || benchmark.prepare_run(),
                    |state| criterion::black_box(benchmark.run(state)),
                    criterion::BatchSize::SmallInput,
                )
            });
        }
    }
}

/// Helper to define the benchmark functions for iai_callgrind.
///
/// Will generate a namespace to use in the `benchmarks` argument to
/// `iai_callgrind::library_benchmark_group!` / `binary_benchmark_group!`.
///
/// Two benchmark instances will be generated:
/// - A "small" benchmark with the smallest size defined in the `sizes` method.
/// - A "big" benchmark with the biggest size defined in the `sizes` method.
///
/// # Arguments
/// - `$namespace`: A unique namespace for the benchmark function, to be passed
///   to the iai group macro.
/// - `$sized_benchmark`: The path to the SizedBenchmark implementer.
macro_rules! sized_iai_benchmark {
    ($namespace:ident, $sized_benchmark:path) => {
        #[iai_callgrind::library_benchmark]
        #[bench::small($sized_benchmark::small())]
        #[bench::big($sized_benchmark::big())]
        fn $namespace(benchmark: impl crate::helper::traits::SizedBenchmark) {
            criterion::black_box(benchmark.run());
        }
    };
}
pub(crate) use sized_iai_benchmark;

/// Helper to define the benchmark functions for iai_callgrind.
///
/// Will generate a namespace to use in the `benchmarks` argument to
/// `iai_callgrind::library_benchmark_group!` / `binary_benchmark_group!`.
///
/// Two benchmark instances will be generated:
/// - A "small" benchmark with the smallest size defined in the `sizes` method.
/// - A "big" benchmark with the biggest size defined in the `sizes` method.
///
/// # Arguments
/// - `$namespace`: A unique namespace for the benchmark function, to be passed
///   to the iai group macro.
/// - `$sized_benchmark`: The path to the SizedBenchmark implementer.
macro_rules! sized_iai_benchmark_with_input {
    ($namespace:ident, $sized_benchmark:path) => {
        #[iai_callgrind::library_benchmark]
        #[bench::small($sized_benchmark::small())]
        #[bench::big($sized_benchmark::big())]
        fn $namespace<Bench: crate::helper::traits::SizedBenchmarkWithInput>(
            benchmark: (Bench, Bench::State),
        ) {
            let (benchmark, state) = benchmark;
            criterion::black_box(benchmark.run(state));
        }
    };
}
pub(crate) use sized_iai_benchmark_with_input;
