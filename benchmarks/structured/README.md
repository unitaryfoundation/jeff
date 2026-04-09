# Structured Benchmark Programs

This directory contains a collection of benchmark programs that use structured control-flow primitives.
These programs should be used as a set of challenges for quantum compilers to drive the development of more advanced compilation techniques.

## Benchmark Program Tracker

This section tracks the current programs of benchmark program implementation and indicates important features about the provided programs.

### Implemented Benchmark Programs

The following table lists the currently implemented benchmark programs and indicates the different formats the program is available in.

| Program                                                          | `jeff` |                   OpenQASM 3                     |
|------------------------------------------------------------------|------|---------------------------------------------------|
| [Quantum Teleportation](./teleportation/README.md)               |  ❌  |     [✔️](./teleportation/teleportation.qasm)     |
| [Grover's Search Algorithm](./grover/README.md)                  |  ❌  |     [✔️](./grover/grover.qasm)                   |
| [GHZ State Preparation (linear)](./ghz-linear/README.md)          |  ❌  |     [✔️](./ghz-linear/ghz-linear.qasm)           |
| [GHZ State Preparation (star)](./ghz-star/README.md)              |  ❌  |     [✔️](./ghz-star/ghz-star.qasm)               |
| [Quantum Fourier Transform (QFT)](./qft/README.md)               |  ❌  |     [✔️](./qft/qft.qasm)                         |
| [Quantum Phase Estimation (QPE)](./qpe/README.md)                |  ❌  |     [✔️](./qpe/qpe.qasm)                         |
| [Iterative Quantum Fourier Transform (iQFT)](./iqft/README.md)   |  ❌  |     [✔️](./iqft/iqft.qasm)                       |
| [Iterative Quantum Phase Estimation (iQPE)](./iqpe/README.md)    |  ❌  |     [✔️](./iqpe/iqpe.qasm)                       |
| [Quantum Multiplexer](./multiplexer/README.md)                   |  ❌  |     [✔️](./multiplexer/multiplexer.qasm)         |

The following table lists the currently implemented benchmark programs together with the structured control-flow primitives they employ.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Teleportation                         |            ❌            |            ❌            |           ❌           |           ❌           |                      ❌                      |                 ✔️                 |            ❌            |     ❌     | [Paper](https://doi.org/10.1103/PhysRevLett.70.1895)                       |       ❌       |    ❌    |
| Grover's Search Algorithm                     |            ✔️            |            ❌            |           ❌           |           ❌           |                      🟦                      |                 ❌                 |            ❌            |     ❌     | [Paper](https://arxiv.org/abs/quant-ph/9605043)                            |       ✔️       |    ❌    |
| GHZ State Preparation (linear)                |            ✔️            |            ❌            |           ✔️           |           ❌           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       |       ✔️       |    ❌    |
| GHZ State Preparation (star)                  |            ✔️            |            ❌            |           ✔️           |           ❌           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       |       ✔️       |    ❌    |
| Quantum Fourier Transform (QFT)               |            ✔️            |            ❌            |           ✔️           |           🟦           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ❌    |
| Quantum Phase Estimation (QPE)                |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ✔️    |
| Iterative Quantum Fourier Transform (iQFT)    |            ✔️            |            ❌            |           ✔️           |           🟦           |                      ❌                      |                 ❌                 |            ❌            |     ✔️     | [Paper](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.76.3228) |       ✔️       |    ❌    |
| Iterative Quantum Phase Estimation (iQPE)     |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ❌                      |                 ❌                 |            ❌            |     ✔️     | [Paper](https://arxiv.org/abs/quant-ph/0610214)                            |       ✔️       |    ✔️    |
| Quantum Multiplexers                          |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ✔️                      |                 ❌                 |            ❌            |     ❌     | [Paper](https://arxiv.org/abs/quant-ph/0410066)                            |       ✔️       |    ✔️    |

#### Symbol Legend

| Symbol | Description |
|--------|-------------|
| ✔️ | Feature is required |
| ❌ | Feature is not used |
| 🟦 | Feature may be used depending on specific implementation |
| ❓ | Requires some further research |

#### Category Details

| Category | Description |
|----------|-------------|
| statically-bounded loops                      | Program uses loops with a constant number of repetitions. |
| dynamically-bounded loops                     | Loop bounds depend on value calculated at runtime. |
| dynamic qubit indexing                        | Gates are applied to qubits with non-constant indices (e.g. loop variable). |
| dynamic classical values                      | Gates use other classical values computed at runtime (e.g. rotation angles taken from arrays). |
| conditionals on originally classical values   | Conditional blocks are used where the condition depends on values that were *not* measurement results. |
| conditionals on measurement results           | Conditional blocks are used where the condition depends on values that depend on measurement results. |
| dynamic qubit allocation                      | Qubits are allocated at runtime (e.g. inside loop bodies). |
| qubit reuse                                   | Existing qubits are reset and reused at runtime. |
| arbitrary-size                                | Instances can be defined generically and parameterized by input parameters to allow for different sizes at runtime. |
| composite                                     | Program combines multiple structured control flow primitives. |

### Unimplemented Benchmark Programs

The following table tracks benchmark programs that have not been implemented yet and that may be implemented through future pull requests.

| Program Type | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references | arbitrary-size | composite
|-----|--------------|-------------------------|--------------------------|-----------------------|--------------|-------------------------|-------------|-----------|--------|----------|----------|
| Block Encoding                                | ❌ | ❌ | ❌ | ❌ | ❌ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1606.02685), [Paper](https://arxiv.org/abs/1806.01838) | ✔️ | ❌ |
| Grover's Search with Weak Measurement         | ❌ | ✔️ | ❌ | ❌ | 🟦 | ✔️ | ❌ | ❌ | [Paper](https://iopscience.iop.org/article/10.1088/2058-9565/ac47f1/meta) | ✔️ | ✔️ |
| QFT adder (quantum input, two registers)      | ✔️ | ❌ | ✔️ | 🟦 | ❌ | ❌ | ❌ | ❌ | [Draper](https://arxiv.org/abs/quant-ph/0008033) | ✔️ | ✔️ |
| QFT adder (classical input, single register)  | ✔️ | ❌ | ✔️ | ✔️|  🟦 | ❌ | ❌ | ❌ | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 3 | ✔️ | ✔️ |
| Controlled multiplication modulo N            | ✔️ | ✔️ | ✔️ | ✔️|  🟦 | ❌ | ❌ | ❌ | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 6 | ✔️ | ✔️ |
| Shor's Algorithm                              | ✔️ | 🟦 | ✔️ | ✔️ | ❌ | ❌ | ❌ | ✔️ | [Paper](https://arxiv.org/abs/quant-ph/9508027) | ✔️ | ✔️ |
| X-Ray Absorption Spectroscopy                 | ✔️ | ❌ | ✔️ | ❓ | ❓ | ❌ | ❌ | ❌ | [Paper](https://arxiv.org/abs/2405.11015), [Tutorial](https://pennylane.ai/qml/demos/tutorial_xas) | ❌ | ✔️ |
| Repeat-Until-Success                          | ❌ | ✔️ | ❌ | ❌ | ❌ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1311.1074) | ❌ | ❌ |
| Quantum Metropolis Sampling                   | ❌ | ✔️ | ✔️ | ❓ | ❓ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/0911.3635) | ❌ | ✔️ |
| ML-QAE                                        | ❌ | ✔️ | ✔️ | ❓ | ❓ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1904.10246) | ❌ | ✔️ |
| Toffoli-heavy Circuits                        | ✔️ | ❌ | ✔️ | ❌ | ❌ | ❌ | ✔️ | ✔️ | [Paper](https://arxiv.org/abs/1904.01671) | ✔️ | ❌ |
| Parallelization with quantum fan-out          | ✔️ | ❌ | ✔️ | 🟦 | ❌ | ❌ | ✔️ | ❌| [Hoyer and Spalek](https://www.theoryofcomputing.org/articles/v001a005/v001a005.pdf), Figs. 4 and 5 | ✔️ | 🟦 |
| Magic State Distillation                      | ✔️ | ✔️ | ✔️ | ❌ | ❌ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/quant-ph/0403025) | ✔️ | ✔️ |
| Logical State Preparation                     | ✔️ | ✔️ | ✔️ | ❌ | ❌ | ✔️ | ❌ | ❌ | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667) | ✔️ | ✔️ |
| Syndrome Measurement and Correction           | ✔️ | ✔️ | ✔️ | ❌ | ❌ | ✔️ | ❌ | ❌ | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667) | ✔️ | ✔️ |
| QAOA with Fixed Repetitions                   | ✔️ | ❌ | ❌ | ✔️ | ❌ | ❌ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1411.4028) | ❌ | ❌ |
| VQE Ansatz with Fixed Repetitions             | ✔️ | ❌ | ❌ | ✔️ | ❌ | ❌ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1304.3061) | ✔️ | ❌ |
| VQE                                           | ✔️ | ❌ | ❌ | ✔️ | ❌ | ✔️ | ❌ | ❌ | [Paper](https://arxiv.org/abs/1304.3061) | ✔️ | ✔️ |
| Measurement-based quantum computation         | 🟦 | ❌ | 🟦 | ✔️ | ❌ | ✔️ | ❌ | 🟦 | [Wikipedia](https://en.wikipedia.org/wiki/One-way_quantum_computer) | ❌ | 🟦 |
