# qpe

This benchmark program is an implementation of Quantum Phase Estimation (QPE) with an arbitrary number of qubits.
It estimates the phase of a Z-rotation, using `n - 1` qubits to store the phase estimate and one target qubit.
The given size parameter `n` specifies the total number of qubits used, including the ancilla qubit.
It must be at least 2.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Phase Estimation (QPE)                |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ✔️    |

## Constraints & Concerns

- The size parameter `n` must be at least 2.
- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but it is still used in this benchmark for potential future compatibility.
