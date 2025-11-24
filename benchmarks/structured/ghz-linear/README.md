# ghz-linear

This benchmark program is an implementation of GHZ state preparation that sets up a fully entangled state by applying `CX`gates linearly to _nearest neighbor_ qubits through a `for` loop.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| GHZ State Preparation (linear)                |            ✔️            |            ❌            |           ✔️           |           ❌           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       |       ✔️       |    ❌    |
