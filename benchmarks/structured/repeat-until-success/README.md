# repeat-until-success

This benchmark program implements the Paetznick--Svore repeat-until-success
gadget with $X$ replaced by $X^{\otimes n}$. Each attempt measures and reuses
one ancilla. After success, the program returns the parity of a
$Y \otimes X^{\otimes(n-1)}$ measurement on the `n` data qubits.

| Program Type         | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                               | arbitrary-size | composite |
| -------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ---------------------------------------- | -------------- | --------- |
| Repeat-Until-Success | ✔️                       | ✔️                        | ✔️                     | ❌                       | ❌                                          | ✔️                                  | ❌                       | ✔️          | [Paper](https://arxiv.org/abs/1311.1074) | ✔️             | ✔️        |
