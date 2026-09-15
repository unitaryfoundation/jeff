# qft-adder-quantum

This benchmark program implements Draper's QFT adder with two `n`-qubit
registers. It prepares the addend as $|+\rangle^{\otimes n}$ and the accumulator
as $|0\cdots01\rangle$, then adds the registers modulo $2^n$. The program
returns both registers.

| Program Type                             | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                       | arbitrary-size | composite |
| ---------------------------------------- | ------------------------ | ------------------------- | ---------------------- | ------------------------ | ------------------------------------------- | ----------------------------------- | ------------------------ | ----------- | ------------------------------------------------ | -------------- | --------- |
| QFT adder (quantum input, two registers) | ✔️                       | ❌                        | ✔️                     | ✔️                       | ❌                                          | ❌                                  | ❌                       | ❌          | [Draper](https://arxiv.org/abs/quant-ph/0008033) | ✔️             | ✔️        |
