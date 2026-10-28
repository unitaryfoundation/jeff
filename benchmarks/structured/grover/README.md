# grover

This benchmark program is an implementation of Grover's algorithm searching for
the state $|111\cdots1\rangle$. The size parameter `n` preserves the original
benchmark convention: the generated phase-oracle program uses `n - 1` search
qubits and no flag qubit.

| Program Type              | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                      | arbitrary-size | composite |
| ------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ----------------------------------------------- | -------------- | --------- |
| Grover's Search Algorithm | ✔️                       | ❌                        | ✔️                     | ❌                       | 🟦                                          | ❌                                  | ❌                       | ❌          | [Paper](https://arxiv.org/abs/quant-ph/9605043) | ✔️             | ❌        |

## Constraints & Concerns

- The size parameter `n` must be at least 3.
