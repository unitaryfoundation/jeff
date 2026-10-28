# controlled-multiplication-modulo-n

This benchmark program implements controlled multiplication by $3$ modulo
$N = 2^{n-1} + 1$. It prepares the control and the `n`-qubit multiplicand in
uniform superposition and stores the product in an `(n + 1)`-qubit accumulator.

| Program Type                       | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                   | arbitrary-size | composite |
| ---------------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ------------------------------------------------------------ | -------------- | --------- |
| Controlled multiplication modulo N | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Beauregard](https://arxiv.org/abs/quant-ph/0205095), Fig. 6 | ✔️             | ✔️        |

## Constraints & Concerns

- The size parameter `n` must be at least 3.
