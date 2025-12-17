# ghz-star

This benchmark program is an implementation of GHZ state preparation that sets up a fully entangled state by applying `CX` gates in a star-like layout to `q[0]` and each other qubit through a `for` loop.

| Program Type                                  | statically-bounded loops | dynamically-bounded loops | dynamic qubit indexing | dynamic classical values | conditionals on originally classical values | conditionals on measurement results | dynamic qubit allocation | qubit reuse | references                                                                 | arbitrary-size | composite |
|-----------------------------------------------|--------------------------|---------------------------|------------------------|--------------------------|---------------------------------------------|-------------------------------------|--------------------------|-------------|----------------------------------------------------------------------------|----------------|-----------|
| GHZ State Preparation (star)                  |            ✔️            |            ❌            |           ✔️           |           ❌           |                      ❌                      |                 ❌                 |            ❌            |     ❌     | [Wikipedia](https://en.wikipedia.org/wiki/GHZ_state)                       |       ✔️       |    ❌    |

## Concerns & Constraints

- The OpenQASM 3.0 specification does not support dynamic qubit indexing, but it is still used in this benchmark for potential future compatibility.
