# Changelog

## [0.2.0](https://github.com/unitaryfoundation/jeff/compare/jeff-format-py-v0.1.0...jeff-format-py-v0.2.0) (2026-08-17)


### ⚠ BREAKING CHANGES

* Fix linearity of while operation ([#72](https://github.com/unitaryfoundation/jeff/issues/72))
* Add size information to `qureg`, `intArray`, and `floatArray` types ([#52](https://github.com/unitaryfoundation/jeff/issues/52))
* Fix order of inputs to `insertIndex` and `insertSlice` ([#50](https://github.com/unitaryfoundation/jeff/issues/50))

### Features

* Add size information to `qureg`, `intArray`, and `floatArray` types ([#52](https://github.com/unitaryfoundation/jeff/issues/52)) ([d4b01fa](https://github.com/unitaryfoundation/jeff/commit/d4b01fabc8948ac482c80f176a7b7614407ff601)), closes [#46](https://github.com/unitaryfoundation/jeff/issues/46)
* Don't print an id for orphan values ([#26](https://github.com/unitaryfoundation/jeff/issues/26)) ([179c364](https://github.com/unitaryfoundation/jeff/commit/179c36476f2b266514c26de1fbb16c1de872e48c))
* Semver versioning for the jeff format ([#41](https://github.com/unitaryfoundation/jeff/issues/41)) ([8325950](https://github.com/unitaryfoundation/jeff/commit/8325950de09dd89cb2fd3ee0744d260f1fb3fa49))


### Bug Fixes

* Fix linearity of while operation ([#72](https://github.com/unitaryfoundation/jeff/issues/72)) ([9e15d25](https://github.com/unitaryfoundation/jeff/commit/9e15d25ddfab27a8f2bd6b21a86d069f9a39d660)), closes [#4](https://github.com/unitaryfoundation/jeff/issues/4)
* Fix order of inputs to `insertIndex` and `insertSlice` ([#50](https://github.com/unitaryfoundation/jeff/issues/50)) ([15a32f4](https://github.com/unitaryfoundation/jeff/commit/15a32f4ad8611f457f7dac7420ea32154f7e202d)), closes [#42](https://github.com/unitaryfoundation/jeff/issues/42)
* Fix Python type helpers ([#54](https://github.com/unitaryfoundation/jeff/issues/54)) ([1aa4f47](https://github.com/unitaryfoundation/jeff/commit/1aa4f474ec6ab2b2e9e50eb43499d8d33815f5fb))
* Re-enable schema load in py library ([#22](https://github.com/unitaryfoundation/jeff/issues/22)) ([4d3cd9c](https://github.com/unitaryfoundation/jeff/commit/4d3cd9ca56d2b8d9cc0781e7bca226e5acd6d9e8))
