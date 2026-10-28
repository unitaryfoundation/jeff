# qft-adder-classical

This benchmark program implements the constant-input form of the QFT adder. It
adds the classical value $5$ to an `n`-qubit accumulator initialized to $1$ and
returns the sum modulo $2^n$.

| Program Type                                 | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                   | arbitrary-size | composite |
| -------------------------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ------------------------------------------------------------ | -------------- | --------- |
| QFT adder (classical input, single register) | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 3 | ✔️             | ✔️        |

## Constraints & Concerns

- The size parameter `n` must be at least 3.
