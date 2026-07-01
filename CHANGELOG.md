# Changelog

This file tracks the changes to the `jeff` exchange format. For changes to the
binding libraries, see the
[Rust CHANGELOG](https://github.com/unitaryfoundation/jeff/blob/main/impl/rs/CHANGELOG.md)
and
[Python CHANGELOG](https://github.com/unitaryfoundation/jeff/blob/main/impl/py/CHANGELOG.md)
files.

The project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-07-02

This version releases a new `verifier` tool as well as two breaking changes. The
full breakdown of the changes can be found below.

- The spec has been updated to clarify that values must be defined before use
  ([#74])
- The regions of the `while` operation have been renamed to `before` and
  `after`. Both regions may arbitrarily modify the state, handing the modifed
  state to each other. This ensures that linearity is preserved ([#72])
- The `doWhile` operation has been removed as its functionality is fully covered
  by the new `while` operation ([#72])
- A new `verifier` tool has been added to check the validity of a `jeff` module.
  The `verifier` crate exports a `verify_file` function that loads and verifies
  a `.jeff` file ([#68], [#72])

## [0.2.0] - 2026-04-14

This version releases two breaking changes. The full breakdown of the changes
can be found below.

- The `qureg`, `intArray`, and `floatArray` types now hold information about the
  size of the underlying structure ([#52])
- The order of inputs to `QuregOp.insertIndex` and `QuregOp.insertSlice` has
  been adapted to be more in line with the order of inputs to
  `IntArrayOp.setIndex` and `FloatArrayOp.setIndex` ([#50])

## [0.1.0] - 2026-02-24

Initial release. Format defined with capnproto `1.3.0`.

<!-- Version links -->

[0.3.0]: https://github.com/unitaryfoundation/jeff/tree/jeff-v0.3.0
[0.2.0]: https://github.com/unitaryfoundation/jeff/tree/jeff-v0.2.0
[0.1.0]: https://github.com/unitaryfoundation/jeff/tree/jeff-v0.1.0

<!-- PR links -->

[#74]: https://github.com/unitaryfoundation/jeff/pull/74
[#72]: https://github.com/unitaryfoundation/jeff/pull/72
[#68]: https://github.com/unitaryfoundation/jeff/pull/68
[#52]: https://github.com/unitaryfoundation/jeff/pull/52
[#50]: https://github.com/unitaryfoundation/jeff/pull/50
