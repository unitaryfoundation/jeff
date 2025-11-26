# qft

This benchmark program is an implementation of Quantum Fourtier Transform (QFT) with an arbitrary number of qubits.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Fourier Transform (QFT)               |            ✔️            |            ❌            |           ✔️           |           🟦           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Nielsen and Chuang](https://doi.org/10.1017/CBO9780511976667)             |       ✔️       |    ❌    |
