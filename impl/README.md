# Protocol implementations

This directory contains the capnproto schema definition and the generated code
for reading and writing *jeff* programs in different languages.

The package major versions match the *jeff* version they implement.

## Schema definition

The serialization schema is defined using the [Cap'n Proto](https://capnproto.org) serialization protocol.

See the [capnp](capnp) directory for the schema definition.

An alternative schema definition is provided in the [protobuf](protobuf) directory.
Although the current implementation is in Cap'n Proto, we may consider switching to protobuf in the future.

## Languages

We publish implementations in the following languages:

-  [C++](cpp)
-  [Rust](rs)
-  [Python](py)

See the [DEVELOPMENT] guide for instructions on how to setup the development environment.

[capnp]: https://github.com/unitaryfoundation/jeff/blob/main/impl/capnp/jeff.capnp
[cpp]: https://github.com/unitaryfoundation/jeff/tree/main/impl/cpp
[rs]: https://github.com/unitaryfoundation/jeff/tree/main/impl/rs
[py]: https://github.com/unitaryfoundation/jeff/tree/main/impl/py
[DEVELOPMENT]: https://github.com/unitaryfoundation/jeff/blob/main/DEVELOPMENT.md
