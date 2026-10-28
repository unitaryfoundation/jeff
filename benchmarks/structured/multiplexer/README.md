# multiplexer

This benchmark program prepares the control qubits in a uniform superposition
and encodes their state in the target qubit with a linear sequence of controlled
`ry` rotations. The size parameter `n` specifies the total number of qubits,
including the target qubit.

| Program Type        | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                      | arbitrary-size | composite |
| ------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ----------------------------------------------- | -------------- | --------- |
| Quantum Multiplexer | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/quant-ph/0410066) | ✔️             | ❌        |

## Constraints & Concerns

- The size parameter `n` must be at least 2.
