# Structured Benchmark Programs

This directory contains a collection of benchmark programs that use structured
control-flow primitives. These programs should be used as a set of challenges
for quantum compilers to drive the development of more advanced compilation
techniques.

## Benchmark Program Tracker

This section tracks benchmark availability and the structured control-flow
features used by each program.

### Implemented Benchmark Programs

The following table lists the available benchmark programs and their checked-in
artifacts.

| Program                                                                              | `jeff`                                                                                                                                                                                                                                                        | QC MLIR reference                                                                    |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| [Quantum Teleportation](./teleportation/README.md)                                   | [✔️](./teleportation/teleportation.jeff)                                                                                                                                                                                                                      | [✔️](./teleportation/teleportation.qc.mlir)                                          |
| [Grover's Search Algorithm](./grover/README.md)                                      | [3](./grover/grover_3.jeff), [5](./grover/grover_5.jeff), [7](./grover/grover_7.jeff)                                                                                                                                                                         | [3](./grover/grover.qc.mlir)                                                         |
| [GHZ State Preparation (linear)](./ghz-linear/README.md)                             | [3](./ghz-linear/ghz-linear_3.jeff), [5](./ghz-linear/ghz-linear_5.jeff), [7](./ghz-linear/ghz-linear_7.jeff)                                                                                                                                                 | [3](./ghz-linear/ghz-linear.qc.mlir)                                                 |
| [GHZ State Preparation (star)](./ghz-star/README.md)                                 | [3](./ghz-star/ghz-star_3.jeff), [5](./ghz-star/ghz-star_5.jeff), [7](./ghz-star/ghz-star_7.jeff)                                                                                                                                                             | [3](./ghz-star/ghz-star.qc.mlir)                                                     |
| [Quantum Fourier Transform (QFT)](./qft/README.md)                                   | [3](./qft/qft_3.jeff), [5](./qft/qft_5.jeff), [7](./qft/qft_7.jeff)                                                                                                                                                                                           | [3](./qft/qft.qc.mlir)                                                               |
| [Quantum Phase Estimation (QPE)](./qpe/README.md)                                    | [3](./qpe/qpe_3.jeff), [5](./qpe/qpe_5.jeff), [7](./qpe/qpe_7.jeff)                                                                                                                                                                                           | [3](./qpe/qpe.qc.mlir)                                                               |
| [Iterative Quantum Fourier Transform (iQFT)](./iqft/README.md)                       | [3](./iqft/iqft_3.jeff), [5](./iqft/iqft_5.jeff), [7](./iqft/iqft_7.jeff)                                                                                                                                                                                     | [3](./iqft/iqft.qc.mlir)                                                             |
| [Iterative Quantum Phase Estimation (iQPE)](./iqpe/README.md)                        | [3](./iqpe/iqpe_3.jeff), [5](./iqpe/iqpe_5.jeff), [7](./iqpe/iqpe_7.jeff)                                                                                                                                                                                     | [3](./iqpe/iqpe.qc.mlir)                                                             |
| [Quantum Multiplexer](./multiplexer/README.md)                                       | [3](./multiplexer/multiplexer_3.jeff), [5](./multiplexer/multiplexer_5.jeff), [7](./multiplexer/multiplexer_7.jeff)                                                                                                                                           | [3](./multiplexer/multiplexer.qc.mlir)                                               |
| [QFT adder (quantum input, two registers)](./qft-adder-quantum/README.md)            | [3](./qft-adder-quantum/qft-adder-quantum_3.jeff), [5](./qft-adder-quantum/qft-adder-quantum_5.jeff), [7](./qft-adder-quantum/qft-adder-quantum_7.jeff)                                                                                                       | [3](./qft-adder-quantum/qft-adder-quantum.qc.mlir)                                   |
| [QFT adder (classical input, single register)](./qft-adder-classical/README.md)      | [3](./qft-adder-classical/qft-adder-classical_3.jeff), [5](./qft-adder-classical/qft-adder-classical_5.jeff), [7](./qft-adder-classical/qft-adder-classical_7.jeff)                                                                                           | [3](./qft-adder-classical/qft-adder-classical.qc.mlir)                               |
| [Controlled multiplication modulo N](./controlled-multiplication-modulo-n/README.md) | [3](./controlled-multiplication-modulo-n/controlled-multiplication-modulo-n_3.jeff), [5](./controlled-multiplication-modulo-n/controlled-multiplication-modulo-n_5.jeff), [7](./controlled-multiplication-modulo-n/controlled-multiplication-modulo-n_7.jeff) | [3](./controlled-multiplication-modulo-n/controlled-multiplication-modulo-n.qc.mlir) |
| [Repeat-Until-Success](./repeat-until-success/README.md)                             | [3](./repeat-until-success/repeat-until-success_3.jeff), [5](./repeat-until-success/repeat-until-success_5.jeff), [7](./repeat-until-success/repeat-until-success_7.jeff)                                                                                     | [3](./repeat-until-success/repeat-until-success.qc.mlir)                             |

> [!NOTE]
> Additional benchmarks will be added on a rolling basis.

The QC MLIR files are representative, human-readable views of the generated
programs for `n = 3`. QC is one of the MLIR dialects in the
[MQT Compiler Collection (`mqt-cc`)](https://mqt.readthedocs.io/projects/core/en/latest/mlir/index.html),
which is part of [MQT Core](https://github.com/munich-quantum-toolkit/core).
These files are provided only for inspection. Use the binary `.jeff` files for
benchmarks. Teleportation has a fixed size and therefore has no `n` suffix.

### Feature Matrix

The following table lists the currently implemented benchmark programs together
with the structured control-flow primitives they employ.

| Program Type                                 | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
| -------------------------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | -------------------------------------------------------------------------- | -------------- | --------- |
| Quantum Teleportation                        | ❌                       | ❌                        | ❌                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://doi.org/10.1103/PhysRevLett.70.1895)                       | ❌             | ❌        |
| Grover's Search Algorithm                    | ✔️                       | ❌                        | ✔️                     | ❌                       | 🟦                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/quant-ph/9605043)                            | ✔️             | ❌        |
| GHZ State Preparation (linear)               | ✔️                       | ❌                        | ✔️                     | ❌                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       | ✔️             | ❌        |
| GHZ State Preparation (star)                 | ✔️                       | ❌                        | ✔️                     | ❌                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       | ✔️             | ❌        |
| Quantum Fourier Transform (QFT)              | ✔️                       | ❌                        | ✔️                     | 🟦                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             | ✔️             | ❌        |
| Quantum Phase Estimation (QPE)               | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             | ✔️             | ✔️        |
| Iterative Quantum Fourier Transform (iQFT)   | ✔️                       | ❌                        | ✔️                     | 🟦                       | ❌                                          | ✔️                                  | ❌                       | ✔️          | [Paper](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.76.3228) | ✔️             | ❌        |
| Iterative Quantum Phase Estimation (iQPE)    | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ✔️                                  | ❌                       | ✔️          | [Paper](https://arxiv.org/abs/quant-ph/0610214)                            | ✔️             | ✔️        |
| Quantum Multiplexer                          | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/quant-ph/0410066)                            | ✔️             | ❌        |
| QFT adder (quantum input, two registers)     | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Draper](https://arxiv.org/abs/quant-ph/0008033)                           | ✔️             | ✔️        |
| QFT adder (classical input, single register) | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 3               | ✔️             | ✔️        |
| Controlled multiplication modulo N           | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 6               | ✔️             | ✔️        |
| Repeat-Until-Success                         | ✔️                       | ✔️                        | ✔️                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ✔️          | [Paper](https://arxiv.org/abs/1311.1074)                                   | ✔️             | ✔️        |

#### Symbol Legend

| Symbol | Description                                              |
| ------ | -------------------------------------------------------- |
| ✔️     | Feature is required                                      |
| ❌     | Feature is not used                                      |
| 🟦     | Feature may be used depending on specific implementation |
| ❓     | Requires some further research                           |

#### Category Details

| Category                                    | Description                                                                                                         |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| statically-bounded loops                    | Program uses loops with a constant number of repetitions.                                                           |
| dynamically-bounded loops                   | Loop bounds depend on value calculated at runtime.                                                                  |
| dynamic qubit indexing                      | Gates are applied to qubits with non-constant indices (e.g. loop variable).                                         |
| dynamic classical values                    | Gates use other classical values computed at runtime (e.g. rotation angles taken from arrays).                      |
| conditionals on originally classical values | Conditional blocks are used where the condition depends on values that were _not_ measurement results.              |
| conditionals on measurement results         | Conditional blocks are used where the condition depends on values that depend on measurement results.               |
| dynamic qubit allocation                    | Qubits are allocated at runtime (e.g. inside loop bodies).                                                          |
| qubit reuse                                 | Existing qubits are reset and reused at runtime.                                                                    |
| arbitrary-size                              | Instances can be defined generically and parameterized by input parameters to allow for different sizes at runtime. |
| composite                                   | Program combines multiple structured control flow primitives.                                                       |

### Unimplemented Benchmark Programs

The following table tracks benchmark programs that have not been implemented yet
and that may be implemented through future pull requests.

| Program Type                          | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                                          | arbitrary-size | composite |
| ------------------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | --------------------------------------------------------------------------------------------------- | -------------- | --------- |
| Block Encoding                        | ❌                       | ❌                        | ❌                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/1606.02685), [Paper](https://arxiv.org/abs/1806.01838)                | ✔️             | ❌        |
| Grover's Search with Weak Measurement | ❌                       | ✔️                        | ❌                     | ❌                       | 🟦                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://iopscience.iop.org/article/10.1088/2058-9565/ac47f1/meta)                           | ✔️             | ✔️        |
| Shor's Algorithm                      | ✔️                       | 🟦                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ✔️          | [Paper](https://arxiv.org/abs/quant-ph/9508027)                                                     | ✔️             | ✔️        |
| X-Ray Absorption Spectroscopy         | ✔️                       | ❌                        | ✔️                     | ❓                       | ❓                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/2405.11015), [Tutorial](https://pennylane.ai/qml/demos/tutorial_xas)  | ❌             | ✔️        |
| Quantum Metropolis Sampling           | ❌                       | ✔️                        | ✔️                     | ❓                       | ❓                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/0911.3635)                                                            | ❌             | ✔️        |
| ML-QAE                                | ❌                       | ✔️                        | ✔️                     | ❓                       | ❓                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/1904.10246)                                                           | ❌             | ✔️        |
| Toffoli-heavy Circuits                | ✔️                       | ❌                        | ✔️                     | ❌                       | ❌                                          | ❌                                  | ✔️                       | ✔️          | [Paper](https://arxiv.org/abs/1904.01671)                                                           | ✔️             | ❌        |
| Parallelization with quantum fan-out  | ✔️                       | ❌                        | ✔️                     | 🟦                       | ❌                                          | ❌                                  | ✔️                       | ❌          | [Hoyer and Spalek](https://www.theoryofcomputing.org/articles/v001a005/v001a005.pdf), Figs. 4 and 5 | ✔️             | 🟦        |
| Magic State Distillation              | ✔️                       | ✔️                        | ✔️                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/quant-ph/0403025)                                                     | ✔️             | ✔️        |
| Logical State Preparation             | ✔️                       | ✔️                        | ✔️                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)                                      | ✔️             | ✔️        |
| Syndrome Measurement and Correction   | ✔️                       | ✔️                        | ✔️                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)                                      | ✔️             | ✔️        |
| QAOA with Fixed Repetitions           | ✔️                       | ❌                        | ❌                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/1411.4028)                                                            | ❌             | ❌        |
| VQE Ansatz with Fixed Repetitions     | ✔️                       | ❌                        | ❌                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/1304.3061)                                                            | ✔️             | ❌        |
| VQE                                   | ✔️                       | ❌                        | ❌                     | ✔️                       | ❌                                          | ✔️                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/1304.3061)                                                            | ✔️             | ✔️        |
| Measurement-based quantum computation | 🟦                       | ❌                        | 🟦                     | ✔️                       | ❌                                          | ✔️                                  | ❌                       | 🟦          | [Wikipedia](https://en.wikipedia.org/wiki/One-way_quantum_computer)                                 | ❌             | 🟦        |

## Generate Other Sizes

The programs were generated with MQT Core. Run the Python recipe from the
repository root with `uv`:

```console
uv run benchmarks/_recipes/structured/generate.py 9
```

The positional arguments select values of `n >= 3`. Without arguments, the
recipe recreates the checked-in programs for `n = 3`, `n = 5`, and `n = 7`. The
benchmark READMEs explain how each family interprets `n`.
