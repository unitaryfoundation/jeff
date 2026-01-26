# iqpe

This benchmark program is an implementation of Iterative Quantum Phase Estimation (iQPE) with an arbitrary number of qubits.
It estimates the phase of a Z-rotation, using `n - 1` qubits to store the phase estimate and one target qubit.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Iterative Quantum Phase Estimation (iQPE)     |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ❌                      |                 ✔️                 |            ❌            |     ✔️     | [Paper](https://arxiv.org/abs/quant-ph/0610214)                            |       ✔️       |    ✔️    |

## Constraints & Concerns

- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but it is still used in this benchmark for potential future compatibility.
