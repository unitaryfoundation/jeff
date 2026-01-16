# iqft

This benchmark program is an implementation of Iterative Quantum Fourier Transform (iQFT) with an arbitrary number of qubits.

The provided program also includes the final swap operations to reverse the order of the qubits.
Therefore, the output qubits will be ordered such that bit `i` (`res[i]`) contains the target state measured for `c[i]`.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Iterative Quantum Fourier Transform (iQFT)    |            ✔️            |            ❌            |           ✔️           |           🟦           |                      ❌                      |                 ✔️                 |            ❌            |     ✔️     | [Paper](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.76.3228) |       ✔️       |    ❌    |

## Constraints & Concerns

- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but it is still used in this benchmark for potential future compatibility.
