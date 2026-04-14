# Changelog

This file tracks the changes to the `jeff` exchange format.
For changes to the binding libraries, see the [Rust CHANGELOG](https://github.com/unitaryfoundation/jeff/blob/main/impl/rs/CHANGELOG.md) and [Python CHANGELOG](https://github.com/unitaryfoundation/jeff/blob/main/impl/py/CHANGELOG.md) files.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-14

This version releases two breaking changes:

- The `qureg`, `intArray`, and `floatArray` types now hold information about the size of the underlying structure ([#52])
- The order of inputs to `QuregOp.insertIndex` and `QuregOp.insertSlice` has been adapted to be more in line with the order of inputs to `IntArrayOp.setIndex` and `FloarArrayOp.setIndex` ([#50])

## [0.1.0] - 2026-02-24

Initial release.
Format defined with capnproto `1.3.0`.

<!-- Version links -->

[0.2.0]: https://github.com/unitaryfoundation/jeff/tree/jeff-v0.2.0
[0.1.0]: https://github.com/unitaryfoundation/jeff/tree/jeff-v0.1.0

<!-- PR links -->

[#52]: https://github.com/unitaryfoundation/jeff/pull/52
[#50]: https://github.com/unitaryfoundation/jeff/pull/50
