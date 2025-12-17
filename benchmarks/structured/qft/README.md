# qft

This benchmark program is an implementation of Quantum Fourier Transform (QFT) with an arbitrary number of qubits.

The provided program also includes the final swap operations to reverse the order of the qubits.
Therefore, the output qubits will be ordered such that qubit `i` (`q[i]`) contains the target state prepared by `U_i`.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Fourier Transform (QFT)               |            ✔️            |            ❌            |           ✔️           |           🟦           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ❌    |
