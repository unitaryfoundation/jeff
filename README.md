<p align="center">
  <img src="https://raw.githubusercontent.com/unitaryfoundation/jeff/docs/images/JEFF_github_logo.png#gh-light-mode-only" width="700px">
    <!--
    Use a relative import for the dark mode image. When loading on alternative services (such as PyPI), this
    will fail automatically and show nothing.
    -->
    <img src="./docs/images/JEFF_github_logo_inverted.png#gh-dark-mode-only" width="700px" onerror="this.style.display='none'" alt=""/>
</p>

*Jeff* is a structured, extensible, and simple interchange format for quantum compilers. Designed
to foster collaboration and accelerate research by providing a common language
for compilers to communicate.

## Features

* Structured representation: First class support for hybrid, structured, and dynamic quantum
  programs. Share the logical intent of a program, not just a low-level gate sequence.

* Efficient: *Jeff* is built to be a high-performance in-memory representation, making it
  fast and easy for compilers to parse, transform, and export.

* Extensible by design: The *Jeff* schema is designed to allow maximum extensibility --- it can be
  easily extended with new features or metadata, ensuring it can grow with the field.

* Bring your own compiler framework: *Jeff* provides a neutral ground for different quantum
  compilers (such as Catalyst, TKET, UCC, and others) to share passes, interoperate seamlessly
  on a single workflow.

## Motivation

The quantum software field is at a critical juncture --- as quantum algorithms become increasingly
sophisticated, quantum program representation is evolving from low-level, gate-centric approaches
to more complex representations that incorporate classical processing, structure, and dynamism.

In particular,

- There are some algorithmic patterns we cannot represent without structure and dynamism
  (for example, repeat-until-success).

- Algorithms inherently contain structure --- by preserving this structure during optimization,
  we can massively improve scalability.

- Thinking beyond simple circuits will allow us to do new things and progress the field.

Compilation and optimization of such programs is crucial to support quantum hardware execution,
however current de-facto interchange formats (such as QIR, and OpenQASM) either lacks the explicit
structure needed for advanced, high-level optimizations, or was not designed for program
optimization.

**This creates a bottleneck for collaboration and makes it difficult to develop and share
sophisticated compiler passes.**

Unlike other common quantum program formats, *Jeff* is not a human-readable source language or a
low-level intermediate representation. It's an in-memory representation designed for
high-performance compiler tools.

Finally, the quantum software, compilation, and hardware development is evolving *rapidly*, and
there is still a *lot* of uncertainty. We don't want to slow down discovery! Jeff will be developed
here, on GitHub, and guided by the needs of quantum software and compilation.

## Getting started

### Schema definition

The serialization schema is defined using the
[Cap'n Proto](https://capnproto.org) serialization protocol. The current version
is defined in [`impl/capnp/jeff.capnp`][capnp].

### Protocol implementations

We provide implementations in various languages for reading and writing *jeff*
programs. See the [`impl`][impl] directory for more information.

## Contributions

*Jeff* is hosted by the [Unitary Foundation](https://unitary.foundation/) and is a collaboration between developers at
[Quantinuum](https://www.quantinuum.com), and [Xanadu](https://www.xanadu.ai).

Your contributions help improve the tool for everyone! There are many ways you can contribute, such as:

- Opening issues to share bugs or request features.
- Taking part in the development discussion and helping us shape the roadmap of *Jeff*.
- Integrating Jeff with quantum compilers.
- Helping us build up a library of interoperable next-gen compiler passes.

If you have questions about contributing, please ask on the Unitary Foundation Discord.

## License

The Jeff project is **free** and **open source**, released under the Apache License, Version 2.0.
