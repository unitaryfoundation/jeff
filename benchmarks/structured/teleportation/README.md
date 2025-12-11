# teleportation

This benchmark program is an implementation of Quantum Teleportation, using conditionals to apply the final corrections.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| Quantum Teleportation                         |            ❌            |            ❌            |           ❌           |           ❌           |                      ❌                      |                 ✔️                 |            ❌            |     ❌     | [Paper](https://doi.org/10.1103/PhysRevLett.70.1895)                       |       ❌       |    ❌    |
