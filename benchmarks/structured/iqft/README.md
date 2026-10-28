# iqft

This benchmark program is an implementation of the semiclassical Quantum Fourier
Transform, called Iterative Quantum Fourier Transform (iQFT) in the benchmark
table. It measures and resets one qubit per iteration and uses earlier
measurement results for phase corrections. The size parameter `n` is the number
of result bits.

| Program Type                               | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
| ------------------------------------------ | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | -------------------------------------------------------------------------- | -------------- | --------- |
| Iterative Quantum Fourier Transform (iQFT) | ✔️                       | ❌                        | ✔️                     | 🟦                       | ❌                                          | ✔️                                  | ❌                       | ✔️          | [Paper](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.76.3228) | ✔️             | ❌        |
