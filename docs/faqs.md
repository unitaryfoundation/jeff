# Frequently asked questions

## Is *Jeff* meant to be an intermediate format that quantum software packages to manipulate?

No. *Jeff* is designed purely to be an exchange format. It is expected that consuming software
frameworks map **Jeff** input to their own intermediate representations for internal maniupation.

## Why design a non-human readable format?

The main goal is to design an *efficient* exchange format that best represents the information
needed for quantum optimizations by compilers, and the most efficient approach is a binary,
non-human readable format.

[Protocol buffers](https://en.wikipedia.org/wiki/Protocol_Buffers) (and derivatives) are a binary
data format initially developed by Google that has been used for similar problems across the
classical domain, and was chosen for *Jeff*.

Human-readable formats have been quite common in the quantum space thus far, but in addition we see
two major reason why they might make less sense going forward:

- We are only just beginning to scale quantum software to FTQC regimes, so have not experienced the
  performance issues associated with (re-)parsing human readable formats, compared to formats
  designed for machine-readability.

- the tooling around IR and exchange formats has not been mature enough, and the best way to
  debug/inspect has often been to simply open and read the file. Improving tooling for debugging
  and visualization should help rectify this.

## How did you decide what goes into the schema?

## Why do we need program structure?

## Why Cap'n Proto?

## Isn't this just *another* format standard?

## Why not format X?

### Why not OpenQASM2?

OpenQASM2 has become the de-facto interchange format in quantum software, but the biggest drawback
has been the lack of program structure — something that we *need* to be a first-class citizen in a
compiler exchange format.

An exchange format that makes it easy to incorporate structure will also allow the field to consider
compilation of structured programs by default.

### Why not OpenQASM3?

OpenQASM3 brings program structure to OpenQASM2, however has not yet seen adoption in the ecosystem
to the extent as OpenQASM2. In addition, OpenQASM3 maintains a focus on human readability, and is
not designed first and foremost for quantum optimization.

In addition, OpenQASM3 has a few quirks that limit its general usability as a compiler exchange
format:

- Lack of extensibility without evolving the specification (a `#pragma` directive is provided, but
  does not easily provide for including general structured information).

- You can only index into arrays using compile-time constants, not dynamic values that may only been
  known at runtime.

- Registers (TODO).

### Why not QIR?

QIR was originally designed as a low-level, hardware-facing IR for optimization, for example using
the QIR Adaptor Tool (QAT). However, QIR today is used less for quantum optimization as it is quite
low-level (missing a lot of the higher-level abstractions we would like to preserve during
compilation), and is predominantly used as a low-level interchange format between software
frameworks and hardware providers.

This can be seen by looking at the various software compilers built on top on the QIR stack such as
CUDA-Q and Catalyst — rather than compiling QIR programs, they instead optimize MLIR, a
higher-level intermediate representation.

Furthermore, relying on QIR as a compilation exchange format introduces a big barrier to entry due
to it depending on the LLVM toolchain — a massive software project that has non-trivial
compatibility concerns, installation, and learning overhead.

### Why not MLIR?


### Why not HUGR?

HUGR is a hybrid quantum-classical program representation introduced by Quantinuum and used by the
TKET and Guppy software libraries. While satisfying a lot of our intended criteria, HUGR itself was
not designed to be an exchange format, and instead is used as an internal intermediate
representation. In addition, HUGR contains advanced features such as type structure that has a high
barrier to entry.

