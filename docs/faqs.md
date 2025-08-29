# Frequently asked questions

## Is *Jeff* meant to be an intermediate format that quantum software packages manipulate?

No. *Jeff* is designed purely to be an exchange format. It is expected that consuming software
frameworks map **Jeff** input to their own intermediate representations for internal manipulation.

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

## Why do we need program structure?

There are two main reasons:

- Because we *need* to (not all algorithmic primitives, an example being repeat-until-success, can
  be represented without structure!), and

- Even when we don't *need* to, preserving structure is necessary for scalability.

Quantum algorithms naturally have structure, even if we aren't used to thinking of them that way.
For example, consider Shor's algorithm: when coded up in Python, we will instinctively use
structure such as if statements, for loops, etc., rather than writing out the finalized list of
gates to be applied. This structure results in a *compressed* program representation compared to
the unrolled list of quantum instructions, so ideally we should design compiler passes to act on
such compressed representations.

In extreme cases, if the program representation does not increase in size as the program scales,
[compilation may be constant-time](https://arxiv.org/abs/2504.12449).

There is still a lot of work to do when it comes to compiling structured programs:

- Often, porting known state-of-the-art compilation techniques to apply to structured programs can
  be highly non-trivial.

- There is tension between maximal optimization and compact program representation. There are still
  a lot of questions we need to consider and resolve when it comes to compiling dynamic, structured
  programs. For example, the more compact the program representation (which is great for
  compilation scalability!) the less information we potentially have up-front to maximally optimize
  programs at compile time. How do we deal with such scenarios?

## How did you decide what goes into the schema?

## Why Cap'n Proto?

## Isn't this just *another* format standard?

## Why not format X?

### Why not OpenQASM2?

[OpenQASM2](https://arxiv.org/abs/1707.03429) has become the de-facto interchange format in quantum software, but the biggest drawback
has been the lack of program structure — something that we *need* to be a first-class citizen in a
compiler exchange format.

An exchange format that makes it easy to incorporate structure will also allow the field to consider
compilation of structured programs by default.

### Why not OpenQASM3?

[OpenQASM3](https://arxiv.org/abs/2104.14722) brings program structure to OpenQASM2, however has not yet seen adoption or tooling
maturity in the ecosystem to the extent as OpenQASM2. In addition, OpenQASM3 maintains a focus on
human readability (requiring string generation and parsing), and is not designed first and foremost for quantum optimization.

Moreover, OpenQASM3 has a few quirks that limit its general usability as a compiler exchange
format:

- Lack of extensibility without evolving the specification (a `#pragma` directive is provided, but
  does not easily allow for including general structured information).

- You can only index into arrays using compile-time constants, not dynamic values that may only been
  known at runtime.

- Registers (TODO).

### Why not QIR?

[QIR](https://www.qir-alliance.org/) was originally designed as a low-level, hardware-facing IR for optimization, for example using
the QIR Adapter Tool (QAT). However, QIR today is used less for quantum optimization as it is quite
low-level (missing a lot of the higher-level abstractions we would like to preserve during
compilation), and is predominantly used as a low-level interchange format between software
frameworks and hardware providers.

This can be seen by looking at the various software compilers built on top on the QIR stack such as
[CUDA-Q](https://github.com/nvidia/cuda-quantum) and [Catalyst](https://github.com/pennylaneai/catalyst) — rather than compiling QIR programs, they instead
optimize MLIR, a higher-level intermediate representation.

Furthermore, relying on QIR as a compilation exchange format introduces a big barrier to entry due
to it depending on the LLVM toolchain — a massive software project that has non-trivial
compatibility concerns, installation, and learning overhead.

### Why not MLIR?

[MLIR (Multi-Level Intermediate Representation)](https://en.wikipedia.org/wiki/MLIR_(software)) is a framework that exists on top of QIR/LLVM, and
permits multiple high-level 'dialects' (IRs tailored to specific domains) to coexist, making it the
framework of choice for most QIR/LLVM compiler stacks such as CUDA-Q and Catalyst.

However, something to note is that MLIR is a *framework*, not a defined format — different compilers
define *multiple* internal/custom dialects that altogether are used to represent a quantum program.
At the moment, there is no clear *shared* set of quantum MLIR dialects that make sense to use more
broadly.

Finally, as per QIR the software tooling remains a big issue. Not all compilers are using LLVM,
which MLIR depends upon, and it introduces the same significant barrier to entry as discussed above
with QIR.

### Why not HUGR?

[HUGR](https://github.com/CQCL/hugr) is a hybrid quantum-classical program representation introduced by Quantinuum and used by the
[TKET](https://github.com/CQCL/tket2) and [Guppy](https://github.com/CQCL/guppylang) software libraries. While satisfying a lot of our intended criteria, HUGR itself was
not designed to be an exchange format, and instead is used as an internal intermediate
representation. In addition, HUGR contains advanced features such as type structure that has a high
barrier to entry.

