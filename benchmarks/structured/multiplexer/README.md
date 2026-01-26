# multiplexer

This benchmark program is an implementation of a Quantum Multiplexer that applies one of 2^(n-1) different `ry` rotations depending on the state of the input register.
The given size parameter `n` specifies the total number of qubits used, including the target qubit.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Multiplexers                          |            ✔️            |            ❌            |           ✔️           |           ✔️           |                      ✔️                      |                 ❌                 |            ❌            |     ❌     | [Paper](https://arxiv.org/abs/quant-ph/0410066)                            |       ✔️       |    ✔️    |

## Constraints & Concerns

- The size parameter `n` must be at least 2.
- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but it is still used in this benchmark for potential future compatibility.
