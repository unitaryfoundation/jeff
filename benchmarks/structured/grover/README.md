# grover

This benchmark program is an implementation of Grover's algorithm searching for the state |111...1>.
The given size parameter `n` specifies the total number of qubits used, including the flag qubit.
It must be at least 2.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Grover's Search Algorithm                     |            ✔️            |            ❌            |           ❌           |           ❌           |                      🟦                      |                 ❌                 |            ❌            |     ❌     | [Paper](https://arxiv.org/abs/quant-ph/9605043)                            |       ✔️       |    ❌    |

## Constraints & Concerns

- The size parameter `n` must be at least 2.
- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but dynamic indexing based on the size parameter is still used in this benchmark for potential future compatibility.
