# *jeff*

*jeff* is a common representation for hybrid quantum programs.

The interchange format is defined as a [Cap'n Proto](https://capnproto.org)
schema. See the [`impl`](https://github.com/unitaryfoundation/jeff/tree/main/impl)
directory for the schema definition and implementation in various languages.

## Collaborators

*jeff* is hosted by the [Unitary Foundation](https://unitary.foundation/) and is a collaboration between developers at
[Quantinuum](https://www.quantinuum.com), and [Xanadu](https://www.xanadu.ai).
We welcome additional contributions and collaborators!

## Schema definition

The serialization schema is defined using the
[Cap'n Proto](https://capnproto.org) serialization protocol. The current version
is defined in [`impl/capnp/jeff.capnp`][capnp].

## Protocol implementations

We provide implementations in various languages for reading and writing *jeff*
programs. See the [`impl`][impl] directory for more information.

[capnp]: https://github.com/unitaryfoundation/jeff/blob/main/impl/capnp/jeff.capnp
[impl]: https://github.com/unitaryfoundation/jeff/tree/main/impl
