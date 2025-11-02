- Feature Name: structured-benchmark-programs
- Start Date: 2025-10-31
- RFC PR: [unitaryfoundation/jeff#0032](https://github.com/unitaryfoundation/jeff/pull/0032)

# Summary
[summary]: #summary

Quantum programs involving structured control flow operations such as `if` and `for` can only be represented in severely limited ways through existing quantum program formats. Qiskit does not allow dynamic qubit indexing, which is crucial for semantic `for` loops. Similarly, while OpenQASM 3 does not explicitly prohibit dynamic indexing, it leaves it open as an optional feature that many backends do not support. Jeff, on the other hand, has the ability to represent such programs, making it the ideal format for expressing a set of structured benchmark programs. These programs can then be used as a set of challenges for existing quantum compilers to drive the development of more advanced compilation techniques.

# Motivation
[motivation]: #motivation

Many programs can be greatly simplified through the use of structured control flow operations.
This includes simple loops for repeated operations, conditionals to implement classically controlled quantum operations in a natural way, and more complex loops and control flow structures that depend on measurement results and access qubits dynamically.

However, a large number of existing quantum compiler toolchains still do not support some or even all of these features.
Proposing a set of such programs as benchmarks can not only help users evaluate the capabilities of different toolchains, but also serve as a motivation for compiler developers to implement these features.

Furthermore, it can also increase the visibility of Jeff as a quantum program format that can express these advanced features, encouraging more users to adopt it for their quantum programming needs.

# Guide-level explanation
[guide-level-explanation]: #guide-level-explanation

A new directory, `benchmarks/structured` is introduced in the Jeff repository.
It provides a set of individual Jeff files that each represent a single structured benchmark program.

In cases where the programs are adaptive in their size, it uses dynamic input parameters to keep the program implementation agnostic of the specifically desired size.
This may include examples such as arbitrarily sized GHZ state preparation, where the number of qubits is specified as an input parameter at runtime.
Similarly, programs that require classical input data such as rotation angles use input parameters to allow users to specify the data at runtime.
An example of this might be a VQA ansatz that is repeated several times using `for` loops.

In contrast, some programs are provided with fixed sizes and parameters, either because they cannot easily be generalized or because they are intended as simpler test scenarios for basic compiler functionality.
Examples of this include simple Quantum Teleportation programs, or predefined instances of Grover's search algorithm.

The modular directory structure allows future adaptations and extensions of the benchmark suite, either by adding other structured programs or by also including entirely new categories of benchmarks.

While this feature may not directly impact the way many users interact with Jeff, it provides a valuable resource for evaluating and improving quantum compilers and test their compatibility with Jeff and advanced quantum programming features.

# Implementation-level explanation
[implementation-level-explanation]: #implementation-level-explanation

The following list outlines the proposed structured benchmark programs to be included in the `benchmarks/structured` directory, along with brief description, grouped by the way they utilize structured control flow:

*Note: this list was created from previous discussions among community members and is open for further suggestions and modifications.*

## Static Loops without Dynamic Qubit Indexing

*This class of benchmark programs utilizes loops (such as `for` and `while`) that **do not** depend on dynamic execution results. Inside the loop bodies, all operations are still statically indexed.*

- *Grover's Search Algorithm*: Oracle and diffusion operations can be applied repeatedly using a fixed-size loop. (https://arxiv.org/abs/quant-ph/9605043)
- *VQE Ansatz with Fixed Repetitions*: A variational ansatz circuit that applies a set of parameterized gates in a loop with a predetermined number of repetitions. ([Peruzzo et al., 2014](https://arxiv.org/abs/1304.3061))
- *QAOA with Fixed Repetitions*: A Quantum Approximate Optimization Algorithm circuit that applies problem and mixer Hamiltonians in a loop with a fixed number of layers. ([Farhi et al., 2014](https://arxiv.org/abs/1411.4028))

## Static Loops with Dynamic Qubit Indexing

*This class of benchmark programs utilizes loops (such as `for` and `while`) that **do not** depend on dynamic execution results. Inside the loop bodies, operations may be dynamically indexed (e.g. based on the loop parameter).*

- *GHZ State Preparation*: A static loop is used to entangle all qubits with each other using `cx` gates where, at each loop index `i`, the `cx` gate is applied between qubit `0` and qubit `i`. ([Wikipedia on GHZ states](https://en.wikipedia.org/wiki/GHZ_state))
- *Quantum Fourier Transform (QFT)*: Nested static loops are used to apply controlled phase rotations between qubits, where the control and target qubits are determined based on the loop index. ([Nielsen and Chuang, 2010](https://doi.org/10.1017/CBO9780511976667))
- *Quantum Phase Estimation (QPE)*: Static loops are used to apply controlled unitary operations and inverse QFT, with qubit indices determined by the loop parameters. ([Nielsen and Chuang, 2010](https://doi.org/10.1017/CBO9780511976667))
- *X-Ray Absorption Spectroscopy*: Simulation of X-Ray Absorption Spectroscopy is implemented using static loops based on [this paper](https://arxiv.org/abs/2405.11015) (https://pennylane.ai/qml/demos/tutorial_xas).

## Dynamic Loops

*This class of benchmark programs utilizes loops (such as `for` and `while`) that **do** depend on dynamic execution results, such as measurement outcomes. Operations may also be dynamically indexed.*

- *Grover's Search with Weak Measurement*: Measurements on an ancilla qubit are utilized to determine whether to continue with another iteration of Grover's search or to stop as amplitude amplification has succeeded. ([Andrés-Martínez et al.](https://iopscience.iop.org/article/10.1088/2058-9565/ac47f1/meta))
- *Repeat-Until-Success*: Specific operations are applied repeatedly until a desired measurement outcome is achieved, indicating that a desired complex operation has been successfully implemented.
- *Quantum Metropolis Sampling*: [Temme et al., 2011](https://arxiv.org/abs/0911.3635)
- *ML-QAE*: [Suzuki et al., 2020](https://arxiv.org/abs/1904.10246)

## Conditionals

*This class of benchmark programs utilizes conditionals (such as `if`) to implement protocols or algorithms.*

- *Quantum Teleportation*: Quantum teleportation is a canonical primitive for quantum communication and distributed computing. It utilizes conditionals based on measurement results to apply the appropriate correction operations. ([Bennett et al., 1993](https://doi.org/10.1103/PhysRevLett.70.1895))
- *Block Encoding*: Block encoding embeds classical data or operators into quantum states. It underpins advanced algorithms like QSVT. It utilizes conditionals to apply different operations. ([Quantum Singular Value Transformation (QSVT)](https://arxiv.org/abs/1806.01838), [Low & Chuang, 2016](https://arxiv.org/abs/1606.02685))

## Mixed Control Flow

*This class of benchmark programs combines loops and conditionals to implement more complex algorithms or protocols.*

- *Quantum Multiplexers*: Quantum multiplexers apply different unitary operations based on the state of control qubits, effectively implementing conditionals in quantum circuits. ([Quantum multiplexers in circuit synthesis](https://arxiv.org/abs/quant-ph/0410066))

## Dynamic Qubit (Re-)Allocation

*This class of benchmark programs allocates qubits dynamically during execution, based on runtime conditions or within loop bodies.*

- *Iterative Quantum Fourier Transform (iQFT)*: Rather than allocating all qubits upfront, just a single qubit is allocated at the start of execution and then reset during each loop iteration of QFT.
- *Iterative Quantum Phase Estimation (iQPE)*: Similar to iQFT, iQPE allocates a single qubit (in addition to the phase qubit "psi") and reuses it across iterations to estimate the phase of a unitary operator.
- *Shor's Algorithm*: The primitives used in Shor's algorithm can similarly be implemented using dynamic qubit reallocation to minimize the total number of qubits required.

## Loosely Coupled Hybrid Programs

*Variational and hybrid algorithms naturally combine quantum circuits with classical optimization loops. They are loosely coupled because the quantum and classical parts interact only at well-defined synchronization points.*

- *VQE*: A variational quantum eigensolver algorithm that uses a classical optimizer to minimize the energy of a parameterized quantum circuit which implements several iterations of some ansatz. ([Peruzzo et al., 2014](https://arxiv.org/abs/1304.3061))
- *QAOA*: A quantum approximate optimization algorithm that uses a classical optimizer to find optimal parameters for a parameterized quantum circuit. It iteratively applies a "problem" and "mixer" operator using loop structures. ([Farhi et al., 2014](https://arxiv.org/abs/1411.4028))

## Fault-Tolerant State Preparation and Error Correction

*Quantum Error Correction (QEC) is one of the most important applications of structured control flow in quantum computing. These benchmark programs implement QEC protocols that involve structured operations at any point in the program.*

- *Magic State Distillation*: Magic state distillation protocols utilize loops and conditionals to iteratively improve the fidelity of magic states, which are essential for fault-tolerant quantum computing. ([Bravyi & Kitaev, 2005](https://arxiv.org/abs/quant-ph/0403025))

---

Each of the benchmark programs listed above should be implemented individually to achieve a comprehensive suite that covers a wide range of structured control flow scenarios.

# Drawbacks
[drawbacks]: #drawbacks

There are several potential drawbacks to consider with this proposal:

- Maintenance Overhead: The addition of a new benchmark suite requires ongoing maintenance to ensure that the benchmarks remain relevant and up-to-date with the latest advancements in quantum computing and compiler technologies.
- Complexity: Introducing structured benchmarks may increase the complexity of the Jeff repository, potentially making it more challenging for new users to navigate and understand the available resources.
- Limited Adoption: If the benchmarks are not widely adopted by the quantum computing community, their impact may be limited, reducing the incentive for compiler developers to implement support for structured control flow.

# Rationale and alternatives
[rationale-and-alternatives]: #rationale-and-alternatives

Potential alternatives include:
- *Implementing structured benchmarks using OpenQASM 3*: While it is possible to represent all desired structured program features in OpenQASM 3, many of these features are only optional and not widely supported by existing backends. Furthermore, using such a representation runs the risk of larger specification changes in the future that could break compatibility.
- *Using more involved quantum programming frameworks like PennyLane*: While frameworks like PennyLane can express structured quantum programs, they often come with additional abstractions and dependencies that are not easily translatable to arbitrary other representations. As the goal of Jeff is to be a widely compatible exchange format, it mitigates this risk by allowing easier compatibility with different representations.
- *Not implementing structured benchmarks at all*: Sooner or later, the quantum computing community will need to address the challenges of structured control flow in quantum programs. By not providing a benchmark suite, we risk slowing down the progress in this area and missing out on opportunities to drive compiler development.

As the reasoning above shows, the proposed design of structured benchmark programs in Jeff is the most effective way to address the need for evaluating and improving quantum compilers' support for advanced control flow features.

# Prior art
[prior-art]: #prior-art

A variety of benchmark suites exist already in the quantum computing community, such as:
- [UCC Bench](https://github.com/unitaryfoundation/ucc-bench): A command-line utility designed to benchmark and compare the performance of various quantum compilers, with a particular focus on the ucc compiler.
- [MQT Bench](https://github.com/munich-quantum-toolkit/bench): A collection of benchmark circuits in qiskit format to evaluate quantum software tools.
- [metriq-gym](https://github.com/unitaryfoundation/metriq-gym): A framework for implementing and running standard quantum benchmarks.

While many of these benchmark suites are widely used and provide valuable insights into quantum compiler performance, they often lack support for structured control flow features such as dynamic loops and conditionals.

To the best of our knowledge, there is currently no widely adopted benchmark suite that specifically targets the evaluation of quantum compilers' support for structured control flow operations, although the topic has been discussed in various community gatherings and conferences.

# Unresolved questions
[unresolved-questions]: #unresolved-questions

- Are there any additional structured benchmark programs that should be included in the initial release?
- How can we best facilitate the adoption of these benchmarks by the quantum computing community?
- Does Jeff already support all necessary features to accurately represent the proposed structured benchmark programs?

# Future possibilities
[future-possibilities]: #future-possibilities

As the field of quantum computing continues to evolve, there are several potential future directions for the structured benchmark programs:

- Addition of further benchmark programs: As structured control flow becomes more prevalent in quantum programming, new algorithms may emerge that utilize these features in novel ways. The benchmark suite can be expanded to include these new algorithms, providing a more comprehensive evaluation of compiler capabilities.
- Addition of further types of structured control flow: Additional benchmark programs may be defined that include further features from classical programming, such as `switch` statements, more complex data structures, exception handling, concurrency, or even function calls and recursion. These features could further challenge quantum compilers and drive advancements in their capabilities.

For the time being, it should already be more than sufficient to cover the types of programs listed above.
The goal should be, first and foremost, to quickly and efficiently set up a solid foundation for the development of compilers with structured control flow support.
