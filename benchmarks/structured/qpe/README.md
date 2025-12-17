# qpe

This benchmark program is an implementation of Quantum Phase Estimation (QPE) with an arbitrary number of qubits.
The given size parameter `n` specifies the total number of qubits used, including the ancilla qubit.
It must be at least 2.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Phase Estimation (QPE)                |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ✔️    |

## Constraints

- The size parameter `n` must be at least 2.
